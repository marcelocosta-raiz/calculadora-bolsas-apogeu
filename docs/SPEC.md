# SPEC — Metas Apogeu

## Dados e cálculo
1. CLI Python recebe base consolidada, ficha e estado anterior explícitos.
2. Ler XLSX fora do repositório, nunca copiar a ficha nem identificadores de alunos para o artefato.
3. Agrupar por unidade, série e aluno internamente; identificar parcelas para não duplicar lançamentos.
4. Incluir captação matriculada e pré-matriculada; excluir cancelados, sem financeiro e bolsa zero. Campos incompletos são pendência, não zero.
5. Realizado é receita contratada líquida de escolaridade e MD /12; verificar se MD já embutido antes de somar. Não usar apenas a primeira parcela: descontos podem variar ao longo do ano.
6. B = meta captação + MD anual/12; Q = meta de alunos; n = alunos elegíveis; S = soma tickets.
7. k = max(Q-n, ceil(Q/2)); R = (B*(n+k)-S)/k quando k>0.
8. Alvo = max(B*1.10, R, alvo do estado anterior da nova base), arredondado para cima no centavo. Sem alunos: piso ou alvo anterior. Q zero: revisão, sem divisão por zero.
9. Flag quando alvo >= B*1.30. Sem aviso de viabilidade do preço, por decisão do usuário em 05/10/2026.
10. Snapshot público inclui somente grupos agregados, hashes de fontes, data e política; sem caminhos locais/PII.
11. Reprocessar a mesma ficha com mesmo estado produz o mesmo resultado. Rejeitar datas anteriores ao estado e alterações de base não aprovadas.

## Interface
Script de agregados separado, carregado antes da interface. Correspondências de curso explícitas e acentos/maiúsculas normalizados. Aba Tickets Metas independente do filtro de preço para incluir Berçário que não possui mensalidade cheia cadastrada. Calculadora filtra ofertas sem metas; usa material mensal, recomenda mensalidade mínima e informa alertas. Preço de Berçário não será inventado.

## Verificação/publicação
Testes Python do cálculo/importação e Node da sintaxe/integração. Build estático com allowlist (HTML, dados e script de metas), evitando publicar docs, scripts e arquivos privados. CI em PR. Preview Vercel via integração Git; se acesso impedir, reportar bloqueio mantendo entrega local testada.

## Integração de 05/10/2026
INTEGRACAO.md prevalece para as páginas separadas, entrada por ticket total e monitor local. Berçário pode ser simulado usando meta e MD validado, sem necessidade de inventar preço cheio.
