"""Local folder -> validated, versioned aggregates. No student data leaves the machine."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from importar_financeiro import build

PUBLIC_FILES = ('index.html', 'dados.js', 'boletins.js', 'metas.js', 'pricing.js',
                'calculadora.js', 'calculadora.html', 'tickets.html')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, suffix='.pending')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_json(path, data):
    atomic_text(path, json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b'0'); stream.flush(); stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise BlockingIOError('Outra sincronizacao em andamento') from error
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def financial_date(name):
    match = re.fullmatch(r'Ficha_Financeira_2027_APOGEU_(\d{2}\.\d{2}\.\d{4})\.xlsx', name, re.I)
    if not match:
        return None
    try:
        return datetime.strptime(match[1], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return None


def fingerprint(path):
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())


def app_fingerprint(repo):
    files = ('index.html', 'dados.js', 'metas.js', 'pricing.js', 'calculadora.js',
             'scripts/verify.mjs', 'scripts/build.mjs', 'scripts/importar_financeiro.py',
             'scripts/sincronizar_financeiro.py')
    return hashlib.sha256(b''.join((repo/name).read_bytes() for name in files)).hexdigest()


def validate_snapshot(data, previous):
    if data['base_hash'] != previous['base_hash'] or data['data_ficha'] < previous['data_ficha']:
        raise ValueError('Base alterada ou ficha anterior')
    old = {m['id']: m for m in previous['metas']}
    if len(data['metas']) != len(old) or {m['id'] for m in data['metas']} != set(old):
        raise ValueError('Cobertura de metas alterada')
    for meta in data['metas']:
        for field in ('ticket_minimo', 'ticket_alvo', 'md_anual', 'alunos', 'soma_tickets'):
            value = meta[field]
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Valor financeiro invalido')
        if (meta['ticket_minimo'] <= 0 or meta['ticket_alvo'] < meta['ticket_minimo']
                or meta['ticket_alvo'] < old[meta['id']]['ticket_alvo']):
            raise ValueError('Piso de ticket reduzido')
    if sum(m['alunos'] for m in data['metas']) != sum(data['status_alunos'].values()):
        raise ValueError('Contagem inconsistente')


def stage_snapshot(repo, state, data, node):
    with tempfile.TemporaryDirectory(dir=state, prefix='validar-') as directory:
        stage = Path(directory)
        for name in PUBLIC_FILES:
            if (repo/name).exists():
                shutil.copy2(repo/name, stage/name)
        (stage/'scripts').mkdir()
        for name in ('verify.mjs', 'build.mjs'):
            shutil.copy2(repo/'scripts'/name, stage/'scripts'/name)
        atomic_json(stage/'boletins.json', data)
        atomic_text(stage/'boletins.js', 'const BOLETINS = '+json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+';\n')
        for script in ('verify.mjs', 'build.mjs'):
            completed = subprocess.run([node, 'scripts/'+script], cwd=stage, capture_output=True, timeout=120)
            if completed.returncode:
                raise ValueError('Validacao do artefato falhou: '+script)
        release = state/'releases'/(data['data_ficha']+'-'+uuid.uuid4().hex)
        # Never overwrite an accepted release, including after a source-code update.
        release.mkdir(parents=True, exist_ok=False)
        atomic_json(release/'boletins.json', data)
        for file in (stage/'dist').iterdir():
            atomic_text(release/file.name, file.read_text(encoding='utf-8'))
        return release


def materialize(repo, release):
    # JSON is bookkeeping; browsers consume only the atomically replaced JS snapshot.
    for name in ('boletins.json', 'boletins.js'):
        if not (repo/name).exists() or (repo/name).read_bytes() != (release/name).read_bytes():
            atomic_text(repo/name, (release/name).read_text(encoding='utf-8'))
    for name in PUBLIC_FILES:
        if not (repo/'dist'/name).exists() or (repo/'dist'/name).read_bytes() != (release/name).read_bytes():
            atomic_text(repo/'dist'/name, (release/name).read_text(encoding='utf-8'))


def refresh_alerts(state, data):
    alerts = [{k: m[k] for k in ('id', 'filial', 'serie', 'ticket_alvo', 'limite_revisao')}
              for m in data['metas'] if m['revisao']]
    atomic_json(state/'alertas-pendentes.json',
                {'data_ficha': data['data_ficha'], 'envio_ativo': False, 'series': alerts})
    return len(alerts)


def sync_once(config):
    repo = Path(config['repository']).resolve()
    state = Path(config['state_dir']).resolve()
    state.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(state/'sync.lock'):
        current_path = state/'current.json'
        current = json.loads(current_path.read_text(encoding='utf-8')) if current_path.exists() else None
        app_hash = app_fingerprint(repo)
        base_file_hash = hashlib.sha256(Path(config['base']).read_bytes()).hexdigest()
        previous_path = state/'releases'/current['release']/'boletins.json' if current else repo/'boletins.json'
        previous = json.loads(previous_path.read_text(encoding='utf-8'))
        if current and current.get('app_hash') == app_hash:
            # Recover a process interrupted after committing the valid snapshot.
            materialize(repo, state/'releases'/current['release'])
            refresh_alerts(state, previous)
        candidates = [(financial_date(p.name), p) for p in Path(config['financial_dir']).glob('*.xlsx')]
        candidates = [(date, p) for date, p in candidates if date]
        if not candidates:
            raise ValueError('Nenhuma ficha Apogeu encontrada')
        date, source = max(candidates, key=lambda item: item[0])
        if date < previous['data_ficha']:
            return {'status': 'older_ignored', 'data_ficha': previous['data_ficha']}
        if time.time()-source.stat().st_mtime < config['stable_seconds']:
            return {'status': 'waiting_stable_file'}
        before = fingerprint(source)
        if (before[2] == previous['ficha_hash'] and date == previous['data_ficha']
                and current and current.get('app_hash') == app_hash):
            if current.get('base_file_hash') == base_file_hash:
                return {'status': 'unchanged', 'data_ficha': date}
        data = build(Path(config['base']), source, previous)
        if fingerprint(source) != before or data['ficha_hash'] != before[2]:
            raise ValueError('Ficha modificada durante a leitura')
        validate_snapshot(data, previous)
        release = stage_snapshot(repo, state, data, config['node'])
        if (app_fingerprint(repo) != app_hash
                or hashlib.sha256(Path(config['base']).read_bytes()).hexdigest() != base_file_hash):
            raise ValueError('Codigo ou base alterados durante a validacao')
        atomic_json(current_path, {'release': release.name, 'accepted_at': stamp(),
                                  'app_hash': app_hash, 'base_file_hash': base_file_hash})
        materialize(repo, release)
        alert_count = refresh_alerts(state, data)
        return {'status': 'updated', 'data_ficha': date, 'metas': len(data['metas']),
                'alunos': sum(m['alunos'] for m in data['metas']), 'alertas': alert_count}


def run(config):
    try:
        result = sync_once(config)
        if result['status'] in ('updated', 'unchanged'):
            from publicar_snapshot import publish
            try:
                snapshot = json.loads((Path(config['repository'])/'boletins.json').read_text(encoding='utf-8'))
                with exclusive_lock(Path(config['state_dir'])/'publish.lock'):
                    result['publication'] = publish(config, snapshot)
            except BlockingIOError:
                result['publication'] = {'status': 'busy'}
            except Exception as error:
                result['publication'] = {'status': 'error', 'error_type': type(error).__name__}
    except BlockingIOError:
        return {'status': 'busy'}
    except Exception as error:
        # Avoid traceback/raw rows in logs: parser exceptions can contain source contents.
        result = {'status': 'error', 'error_type': type(error).__name__, 'checked_at': stamp()}
    result['checked_at'] = stamp()
    atomic_json(Path(config['state_dir'])/'health.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    while True:
        result = run(config)
        if sys.stdout is not None:
            print(json.dumps(result), flush=True)
        if not args.watch:
            raise SystemExit(1 if result['status'] == 'error' else 0)
        time.sleep(config['poll_seconds'])


if __name__ == '__main__':
    main()
