"""Export only validated aggregates through an isolated Git checkout and a CI-gated PR."""
import hashlib
import base64
import json
from pathlib import Path
import shutil
import subprocess


def command(args, cwd, timeout=120):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError('Falha no comando '+args[0]+' '+args[1])
    return result.stdout.strip()


def validate_pr(pr, repository):
    owner, name = repository.split('/')
    if (pr['baseRefName'] != 'master' or pr.get('isCrossRepository')
            or pr['headRepositoryOwner']['login'].lower() != owner.lower()
            or pr['headRepository']['name'].lower() != name.lower()
            or not pr['headRefName'].startswith('codex/financeiro-')
            or not pr['files']
            or not {f['path'] for f in pr['files']}.issubset({'boletins.json', 'boletins.js'})):
        raise ValueError('PR fora do escopo de atualizacao de agregados')


def safe_merge(gh, repository, url, checkout):
    fields='baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,files'
    pr=json.loads(command([gh,'pr','view',url,'--repo',repository,'--json',fields],checkout))
    validate_pr(pr,repository)
    head=pr['headRefOid']
    checks=json.loads(command([gh,'api','repos/'+repository+'/commits/'+head+'/check-runs'],checkout))
    validation=[c for c in checks.get('check_runs',[]) if c['name']=='validate']
    if not validation or not all(c['conclusion']=='success' for c in validation):
        return False
    def content(path, ref):
        response=json.loads(command([gh,'api','repos/'+repository+'/contents/'+path+'?ref='+ref],checkout))
        return base64.b64decode(response['content']).decode('utf-8')
    data=json.loads(content('boletins.json',head))
    script=content('boletins.js',head).strip()
    prefix='const BOLETINS = '
    if not script.startswith(prefix) or not script.endswith(';') or json.loads(script[len(prefix):-1])!=data:
        raise ValueError('JS nao corresponde ao snapshot JSON')
    from sincronizar_financeiro import validate_snapshot
    validate_snapshot(data,json.loads(content('boletins.json','master')))
    command([gh,'pr','merge',url,'--squash','--match-head-commit',head],checkout)
    return True


def publish(config, snapshot):
    if not config.get('publish_enabled', False):
        return {'status': 'disabled_pending_release_approval'}
    repository = config['repository_slug']
    if not repository or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./' for c in repository):
        raise ValueError('Repositorio invalido')
    checkout = Path(config['publish_dir']).resolve()
    checkout.parent.mkdir(parents=True, exist_ok=True)
    git = shutil.which('git')
    gh = shutil.which('gh')
    if not git or not gh:
        raise RuntimeError('Git e GitHub CLI precisam estar disponiveis')
    if not checkout.exists():
        command([git, 'clone', '--branch', 'master', 'https://github.com/'+repository+'.git', str(checkout)], checkout.parent)
    expected_origin='https://github.com/'+repository+'.git'
    if command([git,'remote','get-url','origin'],checkout).lower()!=expected_origin.lower():
        raise RuntimeError('Origem Git inesperada; publicacao bloqueada')
    dirty=command([git,'status','--porcelain'],checkout)
    if dirty:
        # This checkout belongs exclusively to the publisher. Restore ONLY aggregate
        # files after an interrupted run; any other edit requires human inspection.
        changed={line[3:] for line in dirty.splitlines()}
        if not changed.issubset({'boletins.json','boletins.js'}):
            raise RuntimeError('Checkout de publicacao tem alteracoes fora do escopo')
        command([git,'restore','--source=HEAD','--staged','--worktree','--','boletins.json','boletins.js'],checkout)
    prs = json.loads(command([gh, 'pr', 'list', '--repo', repository, '--state', 'open',
                             '--json', 'url,headRefName,headRefOid'], checkout))
    pending = [pr for pr in prs if pr['headRefName'].startswith('codex/financeiro-')]
    if pending:
        if config.get('auto_merge', False):
            if safe_merge(gh,repository,pending[0]['url'],checkout):
                return {'status': 'merged', 'pr': pending[0]['url']}
        return {'status': 'pending_ci_or_merge', 'pr': pending[0]['url']}
    command([git, 'fetch', 'origin', 'master'], checkout)
    command([git, 'switch', 'master'], checkout)
    command([git, 'merge', '--ff-only', 'origin/master'], checkout)
    # Never publish through an old app that lacks the integrated calculator.
    if not (checkout/'calculadora.js').exists():
        raise RuntimeError('Integracao ainda nao aprovada em master')
    live = json.loads((checkout/'boletins.json').read_text(encoding='utf-8'))
    if live == snapshot:
        return {'status': 'already_published'}
    from sincronizar_financeiro import validate_snapshot
    validate_snapshot(snapshot, live)
    canonical = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    branch = 'codex/financeiro-'+snapshot['data_ficha']+'-'+digest
    local = command([git, 'branch', '--list', branch], checkout)
    command([git, 'switch', branch] if local else [git, 'switch', '-c', branch], checkout)
    from sincronizar_financeiro import atomic_text
    atomic_text(checkout/'boletins.json', canonical)
    atomic_text(checkout/'boletins.js', 'const BOLETINS = '+canonical.rstrip()+';\n')
    command([config['node'], 'scripts/verify.mjs'], checkout)
    command([config['node'], 'scripts/build.mjs'], checkout)
    command([git, 'add', 'boletins.json', 'boletins.js'], checkout)
    staged = command([git, 'diff', '--cached', '--name-only'], checkout).splitlines()
    if staged:
        if not set(staged).issubset({'boletins.json', 'boletins.js'}):
            raise RuntimeError('Arquivo fora da allowlist')
        command([git, 'commit', '-m', 'chore: atualiza ficha Apogeu '+snapshot['data_ficha']], checkout)
    command([git, 'push', '-u', 'origin', branch], checkout)
    body = ('Atualiza somente os agregados por escola e serie da ficha '+snapshot['data_ficha']
            +'. Fontes individuais permanecem locais. Pisos anteriores preservados.\n\n'
            '- [x] Validacao local do snapshot e build\n- [ ] CI aprovado antes do merge\n')
    body_path = checkout.parent/'snapshot-pr-body.md'
    atomic_text(body_path, body)
    url = command([gh, 'pr', 'create', '--repo', repository, '--base', 'master', '--head', branch,
                   '--title', 'chore: atualiza ficha Apogeu '+snapshot['data_ficha'], '--body-file', str(body_path)], checkout)
    # Auto-merge is never used to bypass missing/failed checks. Disabled until rollout approval.
    if config.get('auto_merge', False):
        safe_merge(gh,repository,url,checkout)
    return {'status': 'pr_created', 'pr': url}
