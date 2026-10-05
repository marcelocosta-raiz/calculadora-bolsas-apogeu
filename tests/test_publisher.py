import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from publicar_snapshot import validate_pr, publish


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.repository='marcelocosta-raiz/calculadora-bolsas-apogeu'
        self.pr={'baseRefName':'master','isCrossRepository':False,
                 'headRepositoryOwner':{'login':'marcelocosta-raiz'},
                 'headRepository':{'name':'calculadora-bolsas-apogeu'},
                 'headRefName':'codex/financeiro-2026-10-01',
                 'files':[{'path':'boletins.json'},{'path':'boletins.js'}]}

    def test_aggregate_only_pr(self):
        validate_pr(self.pr,self.repository)

    def test_rejects_source_changes_wrong_base_and_foreign_repo(self):
        cases=[('files',[{'path':'index.html'}]),('files',[]),('baseRefName','other'),
               ('isCrossRepository',True),('headRepositoryOwner',{'login':'other'}),
               ('headRepository',{'name':'other'}),('headRefName','other')]
        for field,value in cases:
            with self.subTest(field=field,value=value):
                pr=copy.deepcopy(self.pr);pr[field]=value
                with self.assertRaises(ValueError):validate_pr(pr,self.repository)

    def test_disabled_does_not_access_git_or_network(self):
        self.assertEqual(publish({'publish_enabled':False},None),
                         {'status':'disabled_pending_release_approval'})


if __name__=='__main__':unittest.main()
