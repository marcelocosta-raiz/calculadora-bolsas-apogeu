"""Importação local: XLSX privado -> agregados públicos, sem dados pessoais."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import openpyxl

MONTHS = Decimal(12)
MINIMUM = Decimal('1.10')
ALERT = Decimal('1.30')
CENT = Decimal('.01')
COURSES = {'PRE-MILITAR AFA/EFOMM': 'AFA / Naval',
           'PRE-MILITAR CN EPCAR': 'CN / EPCAr',
           'PRE-MILITAR ESPCEX': 'EsPCEx',
           'PRE-VESTIBULAR - MEDICINA': 'Medicina',
           'PRE-VESTIBULAR': 'Pré-Vestibular'}


def norm(value):
    return ' '.join(unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().upper().split())


def decimal(value):
    if value is None or value == '':
        raise ValueError('Valor financeiro ausente')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Valor financeiro não finito')
    return result


def ceil_money(value):
    return float(value.quantize(CENT, rounding=ROUND_CEILING))


def calculate(base, quantity, tickets, previous=None):
    if base <= 0 or quantity < 0 or int(quantity) != quantity:
        raise ValueError('Meta inválida')
    count = len(tickets)
    horizon = max(int(quantity) - count, (int(quantity) + 1) // 2)
    total = sum(tickets, Decimal(0))
    recovery = (base * (count + horizon) - total) / horizon if horizon else None
    target = max(base * MINIMUM, recovery or Decimal(0), decimal(previous) if previous is not None else Decimal(0))
    applied = ceil_money(target)
    return {'alunos': count, 'ticket_realizado': float(total / count) if count else None,
            'soma_tickets': float(total), 'horizonte': horizon,
            'ticket_recuperacao': ceil_money(recovery) if recovery is not None else None,
            'ticket_minimo': ceil_money(base * MINIMUM), 'ticket_alvo': applied,
            'limite_revisao': ceil_money(base * ALERT),
            'revisao': decimal(applied) >= base * ALERT,
            'sem_horizonte': not bool(horizon)}


def build(base_path, financial_path, previous=None):
    consolidated = json.loads(base_path.read_text(encoding='utf-8'))
    metas = [m for m in consolidated['metas'] if m['marca'] == 'apogeu']
    definition = [{k: m[k] for k in ('id', 'escola', 'segmento', 'serie', 'serie_calculadora',
                  'mensalidade_meta_captacao', 'md_anual', 'meta_alunos_captacao')} for m in metas]
    base_hash = hashlib.sha256(json.dumps(definition, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', financial_path.name)
    if not date_match:
        raise ValueError('Nome de ficha sem data identificável')
    date = datetime.strptime(date_match[1], '%d.%m.%Y').date().isoformat()
    prior = {}
    if previous:
        if previous['base_hash'] != base_hash:
            raise ValueError('Base alterada: revisão explícita necessária antes de migrar novamente')
        if previous['data_ficha'] > date:
            raise ValueError('Ficha anterior ao estado atual')
        prior = {r['id']: r['ticket_alvo'] for r in previous['metas']}
    by_key = {(norm(m['escola']), norm(m['serie'])): m for m in metas}
    workbook = openpyxl.load_workbook(financial_path, read_only=True, data_only=True)
    groups = defaultdict(list)
    try:
        iterator = workbook.active.values
        headers = next(iterator)
        required = {'CODFILIAL', 'RA', 'FILIAL', 'SERIE', 'TIPO MATRICULA', 'STATUS_PERIODO_LETIVO',
                    'SITUACAO_CONTRATO', 'CODCONTRATO', 'SERVICO', 'PARCELA', 'COTA',
                    'REF_FINANCEIRO', 'VALORORIGINAL', 'BOLSA/DEDUÇÕES'}
        if not required.issubset(headers):
            raise ValueError('Cabeçalho financeiro incompatível')
        for values in iterator:
            row = dict(zip(headers, values))
            if norm(row['TIPO MATRICULA']) != 'MATRICULA':
                continue
            if row['RA'] is None:
                raise ValueError('Identificador de aluno ausente')
            groups[(row['CODFILIAL'], row['RA'], norm(row['SERIE']))].append(row)
    finally:
        workbook.close()
    tickets = defaultdict(list)
    exclusions = defaultdict(Counter)
    ignored = Counter()
    statuses = Counter()
    for rows in groups.values():
        first = rows[0]
        school = norm(first['FILIAL']).removeprefix('APOGEU ')
        series = norm(COURSES.get(norm(first['SERIE']), first['SERIE']))
        meta = by_key.get((school, series))
        if meta is None:
            ignored[(school, series)] += 1
            continue
        key = meta['id']
        if any(norm(r['SITUACAO_CONTRATO']) != 'ATIVO' for r in rows):
            exclusions[key]['contrato_inativo'] += 1
            continue
        if any(norm(r['STATUS_PERIODO_LETIVO']) not in ('MATRICULADO', 'PRE-MATRICULADO') for r in rows):
            exclusions[key]['status_nao_elegivel'] += 1
            continue
        tuition = [r for r in rows if any(s in norm(r['SERVICO']) for s in ('MENSALIDADE', 'ANUIDADE'))]
        material = [r for r in rows if norm(r['SERVICO']).startswith('MD ')]
        financial = tuition + material
        if not tuition or any(r['PARCELA'] is None or r['REF_FINANCEIRO'] is None for r in financial):
            exclusions[key]['sem_parcela_gerada'] += 1
            continue
        # A zero deduction on material alone does not make a tuition scholarship zero.
        try:
            monthly = [r for r in tuition if 'MENSALIDADE' in norm(r['SERVICO'])]
            annual = [r for r in tuition if 'ANUIDADE' in norm(r['SERVICO'])]
            if (monthly and annual) or len(annual) > 1:
                raise ValueError('Escolaridade anual e mensal sobrepostas')
            if meta['segmento'] != 'CL' and not annual and len(monthly) != int(MONTHS):
                raise ValueError('Escolaridade com parcelas incompletas')
            discounts = [decimal(r['BOLSA/DEDUÇÕES']) for r in tuition]
            if all(d == 0 for d in discounts):
                exclusions[key]['bolsa_zero'] += 1
                continue
            if decimal(meta['md_anual']) > 0 and not material:
                exclusions[key]['material_sem_financeiro'] += 1
                continue
            seen = {}
            for row in financial:
                installment = (row['CODCONTRATO'], row['SERVICO'], row['PARCELA'], row['COTA'])
                amount = decimal(row['VALORORIGINAL']) - decimal(row['BOLSA/DEDUÇÕES'])
                if amount < 0:
                    raise ValueError('Parcela líquida negativa')
                if installment in seen:
                    raise ValueError('Parcela duplicada ou renegociada requer revisão')
                seen[installment] = amount
            if len({r['CODCONTRATO'] for r in tuition}) != 1:
                raise ValueError('Contratos de escolaridade ambíguos')
            tickets[key].append(sum(seen.values(), Decimal(0)) / MONTHS)
            statuses[norm(first['STATUS_PERIODO_LETIVO'])] += 1
        except (ValueError, ArithmeticError):
            exclusions[key]['financeiro_pendente_revisao'] += 1
    result = []
    for meta in metas:
        base = decimal(meta['mensalidade_meta_captacao']) + decimal(meta['md_anual']) / MONTHS
        calc = calculate(base, meta['meta_alunos_captacao'], tickets[meta['id']], prior.get(meta['id']))
        result.append({'id': meta['id'], 'filial': meta['escola'], 'segmento': meta['segmento'],
                       'serie': meta['serie_calculadora'], 'serie_fonte': meta['serie'],
                       'ticket_meta': float(base), 'md_anual': meta['md_anual'],
                       'meta_alunos': meta['meta_alunos_captacao'],
                       'excluidos': dict(exclusions[meta['id']]), **calc})
    return {'versao': 1, 'base_hash': base_hash, 'data_ficha': date,
            'ficha_hash': hashlib.sha256(financial_path.read_bytes()).hexdigest(),
            'metas': result, 'status_alunos': dict(statuses),
            'grupos_sem_meta': [{'escola': k[0], 'serie': k[1], 'alunos': v} for k, v in sorted(ignored.items())],
            'email_ativo': False, 'atualizacao': 'Carga validada da ficha financeira',
            'regras': {'margem': float(MINIMUM - 1), 'alerta': float(ALERT - 1),
                       'inclui_pre_matriculados': True, 'exclui_bolsa_zero': True}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--ficha', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    previous = json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else None
    data = build(args.base, args.ficha, previous)
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    pending = args.output.with_suffix('.tmp')
    pending.write_text(content + '\n', encoding='utf-8')
    assert json.loads(pending.read_text(encoding='utf-8')) == data
    pending.replace(args.output)
    args.output.with_suffix('.js').write_text('const BOLETINS = ' + content + ';\n', encoding='utf-8')
    print(json.dumps({'metas': len(data['metas']), 'alunos': sum(r['alunos'] for r in data['metas']),
                      'exclusoes': dict(sum((Counter(r['excluidos']) for r in data['metas']), Counter())),
                      'sem_meta': data['grupos_sem_meta'], 'status': data['status_alunos'],
                      'alertas': sum(r['revisao'] for r in data['metas'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
