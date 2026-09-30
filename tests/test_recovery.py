"""Regressões numéricas do exemplo real QI Valqueire, aprovado no projeto."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from importar_financeiro import calculate


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.base = D('1407.8845325828186')
        # A fórmula usa n e soma: média real repetida representa os mesmos agregados.
        self.tickets = [D('19949.16666666666666666666667') / 17] * 17

    def test_real_valqueire_half_target_after_goal(self):
        result = calculate(self.base, 15, self.tickets)
        self.assertEqual(result['horizonte'], 8)
        self.assertEqual(result['ticket_alvo'], 1906.00)
        self.assertEqual(result['limite_revisao'], 1830.25)
        self.assertTrue(result['revisao'])

    def test_preserves_new_floor_and_repeated_load(self):
        first = calculate(self.base, 15, self.tickets)
        again = calculate(self.base, 15, self.tickets, first['ticket_alvo'])
        self.assertEqual(first, again)
        preserved = calculate(self.base, 15, self.tickets, D('2404.11'))
        self.assertEqual(preserved['ticket_alvo'], 2404.11)

    def test_empty_population_uses_margin_without_legacy(self):
        result = calculate(self.base, 15, [])
        self.assertEqual(result['horizonte'], 15)
        self.assertIsNone(result['ticket_realizado'])
        self.assertEqual(result['ticket_alvo'], 1548.68)
        self.assertFalse(result['revisao'])

    def test_no_division_by_zero(self):
        result = calculate(self.base, 0, [])
        self.assertTrue(result['sem_horizonte'])
        self.assertIsNone(result['ticket_recuperacao'])
        self.assertEqual(result['ticket_alvo'], 1548.68)

    def test_invalid_targets_fail(self):
        with self.assertRaises(ValueError):
            calculate(self.base, -1, [])
        with self.assertRaises(ValueError):
            calculate(D(0), 15, [])


if __name__ == '__main__':
    unittest.main()
