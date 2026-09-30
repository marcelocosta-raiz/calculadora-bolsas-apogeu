# Fonte de Dados — Calculadora de Bolsas Apogeu 2027

## Tabela de Preços (`DADOS`)

| Campo | Descrição | Fonte |
|-------|-----------|-------|
| `mensalidade` | Mensalidade bruta 2027 por série/turno | Tabela de preços Apogeu 2027 |
| `material` | Material didático anual 2027 | Tabela de preços Apogeu 2027 |
| `anuidade` | Anuidade = mensalidade × 12 | Calculado |

## Metas (`METAS`)

**Arquivo-fonte:** `Downloads/Metas_2027_Apogeu novas.xlsx`  
**Aba:** `Detalhe por Série`  
**Atualizado em:** 2026-09-29

### Fórmula do ticket

```
ticket_meta = mensalidade_media_captacao + (material_anual / 12)
ticket_alvo = ticket_meta × 1,10
```

| Campo xlsx | Coluna | Descrição |
|-----------|--------|-----------|
| `Mensalidade média captação` | col L | Ticket médio esperado para alunos novos, considerando bolsistas |
| `material_anual / 12` | de `DADOS` | Parcela mensal do material didático da série |

### Regras de mapeamento

- **EI / EF1 / EF2 / EM**: match direto `(filial, segmento, série)` entre xlsx e DADOS
- **EI Berçário (GS Ferreira Guimarães)**: sem entrada própria em DADOS → usa material do Infantil 1 da mesma unidade
- **CL (cursos livres)**: nomes no xlsx são agrupamentos; mapeamento para série em DADOS:

| Nome no xlsx | Série em DADOS |
|-------------|----------------|
| AFA / Naval | Pré-Militar AFA EFOMM |
| CN / EPCAr | Pré-Militar CN EPCAr |
| ESA | Pré-Militar ESA |
| EsPCEx | Pré-Militar EsPCEx |
| IME / ITA | Pré-Militar ITA IME |
| Medicina | PV - Medicina |
| Pré-Vestibular | PV |

### O que NÃO é o ticket_meta

- ~~Mensalidade média total~~ — inclui renovação e captação ponderados; não reflete meta para novos alunos
- ~~Mensalidade bruta~~ — sem desconto de bolsa
- ~~Anuidade / 12~~ — não inclui material

## Histórico de versões

| Data | Alteração | Fonte |
|------|-----------|-------|
| 2026-09-25 | Metas usando `mensalidade_media_total` (incorreto) | `Metas_2027_Apogeu novas.xlsx` |
| 2026-09-29 | Corrigido: `ticket_meta = mensalidade_media_captacao + material/12` | `Metas_2027_Apogeu novas.xlsx` |
