"""Integration smoke using the user's real sources, in a disposable private checkout."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from sincronizar_financeiro import sync_once, run


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    args=parser.parse_args()
    source=json.loads(args.config.read_text(encoding='utf-8-sig'))
    real_repo=Path(source['repository'])
    parent=Path(source['state_dir']).parent
    with tempfile.TemporaryDirectory(dir=parent,prefix='teste-real-') as directory:
        root=Path(directory).resolve()
        assert root.is_relative_to(parent.resolve())
        repo=root/'repo';repo.mkdir()
        for name in ('index.html','dados.js','boletins.json','boletins.js','metas.js','pricing.js','calculadora.js'):
            shutil.copy2(real_repo/name,repo/name)
        shutil.copytree(real_repo/'scripts',repo/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
        config={**source,'repository':str(repo),'state_dir':str(root/'state'),'publish_enabled':False}
        local_base=root/'base.json';shutil.copy2(source['base'],local_base);config['base']=str(local_base)
        first=sync_once(config)
        assert first['status']=='updated',first
        second=sync_once(config)
        assert second['status']=='unchanged',second
        # Simulate interruption after selecting the valid release but before writing all assets.
        damaged=repo/'dist'/'calculadora.js'
        expected=damaged.read_bytes();damaged.write_text('interrupted',encoding='utf-8')
        repaired=sync_once(config)
        assert repaired['status']=='unchanged' and damaged.read_bytes()==expected
        alerts=root/'state'/'alertas-pendentes.json'
        expected_alerts=alerts.read_bytes();alerts.write_text('{}',encoding='utf-8')
        assert sync_once(config)['status']=='unchanged'
        assert alerts.read_bytes()==expected_alerts
        prior=(root/'state'/'current.json').read_bytes()
        prior_json=(repo/'boletins.json').read_bytes()
        original_base=local_base.read_bytes()
        base=json.loads(original_base)
        for meta in base['metas']:
            if meta['marca']=='apogeu':
                meta['mensalidade_meta_captacao']+=1
                break
        local_base.write_text(json.dumps(base),encoding='utf-8')
        assert run(config)['status']=='error'
        assert (root/'state'/'current.json').read_bytes()==prior
        local_base.write_bytes(original_base)
        # An invalid app update must fail build before promoting any data.
        with (repo/'index.html').open('a',encoding='utf-8') as stream:
            stream.write('<script>syntax error !!</script>')
        failed=run(config)
        assert failed['status']=='error',failed
        assert (root/'state'/'current.json').read_bytes()==prior
        assert (repo/'boletins.json').read_bytes()==prior_json
        assert damaged.read_bytes()==expected
        print(json.dumps({'real_import':first,'repeat':second['status'],
                          'interruption_repaired':True,'failed_build_preserves_state':True,
                          'base_change_blocked':True,'alerts_repaired':True}))


if __name__=='__main__':main()
