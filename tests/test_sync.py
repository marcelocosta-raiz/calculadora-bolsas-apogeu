import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sincronizar_financeiro import financial_date, validate_snapshot, exclusive_lock, atomic_json


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((Path(__file__).resolve().parents[1]/'boletins.json').read_text(encoding='utf-8'))

    def test_only_complete_apogeu_filename(self):
        self.assertEqual(financial_date('Ficha_Financeira_2027_APOGEU_01.10.2026.xlsx'),'2026-10-01')
        for name in ['~$Ficha_Financeira_2027_APOGEU_01.10.2026.xlsx',
                     'Ficha_Financeira_2027_QI_01.10.2026.xlsx',
                     'Ficha_Financeira_2027_APOGEU_01.10.2026_ALUNOS NOVOS.xlsx',
                     'Ficha_Financeira_2027_APOGEU_32.10.2026.xlsx']:
            self.assertIsNone(financial_date(name))

    def test_actual_snapshot_and_repeat(self):
        validate_snapshot(self.data,self.data)

    def test_no_target_decrease(self):
        changed=copy.deepcopy(self.data)
        changed['metas'][0]['ticket_alvo']-=.01
        with self.assertRaises(ValueError):validate_snapshot(changed,self.data)

    def test_old_date_base_change_or_missing_series_fail(self):
        for key,value in [('data_ficha','2020-01-01'),('base_hash','changed'),('metas',self.data['metas'][:-1])]:
            changed=copy.deepcopy(self.data);changed[key]=value
            with self.assertRaises(ValueError):validate_snapshot(changed,self.data)

    def test_invalid_number_or_count_fails(self):
        for key,value in [('ticket_alvo',float('nan')),('alunos',-1),('ticket_minimo',0)]:
            changed=copy.deepcopy(self.data);changed['metas'][0][key]=value
            with self.assertRaises(ValueError):validate_snapshot(changed,self.data)

    def test_lock_and_atomic_write(self):
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock'
            with exclusive_lock(lock):
                with self.assertRaises(BlockingIOError):
                    with exclusive_lock(lock):pass
            path=Path(directory)/'state.json'
            atomic_json(path,self.data)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),self.data)

if __name__=='__main__':unittest.main()
