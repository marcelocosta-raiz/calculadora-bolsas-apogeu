# BOLETINS DE DESCONTOS — Apogeu

## Objetivo
Orientar admissões com metas de captação por unidade/série calculadas a partir das fichas financeiras reais, incluindo pré-matriculados. Preservar a identidade da calculadora existente.

## Escopo desta entrega
- Importação local automática da ficha mais recente e publicação somente de agregados via PR/CI.
- Meta-base de captação + MD anual/12; margem mínima de 10%.
- Recuperação pelo maior entre saldo de captação e metade da meta original arredondada para cima.
- Migração sem piso legado; alvos posteriores nunca diminuem.
- Nova aba Tickets Metas com filtros, origem/data, contagem, realizado, alvo e revisão a partir de base +30%.
- Calculadora usa os mesmos alvos; ofertas sem meta não participam da negociação.
- Bolsões e condições vencidas de 30/09 removidos.

## Entregas posteriores
Monitor local implementado conforme INTEGRACAO.md. E-mail depende do aceite dos termos e configuração do serviço; não exibir envio como ativo enquanto indisponível.

## Aceite
Dados pessoais não são publicados. Carga repetida não aumenta os alvos. Erros preservam a última carga válida. Valores conferidos contra a ficha, testes de limites e de interface aprovados antes de publicar preview via PR.
