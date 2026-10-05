# Operação — atualização das fichas Apogeu

## Rotina local
A tarefa Windows `BoletinsDescontos-Apogeu` inicia no login do usuário e verifica a pasta configurada a cada 60 segundos. Precisa deste computador ligado e da sessão do usuário disponível. Não depende de manter a conversa aberta.

Somente nomes completos `Ficha_Financeira_2027_APOGEU_DD.MM.AAAA.xlsx` são aceitos. Arquivos temporários e relatórios parciais ficam fora. A rotina aguarda estabilidade do arquivo por 30 segundos, valida a carga e preserva a última versão válida em caso de falha. A ficha mais recente é escolhida pela data no nome, não pela ordem de download.

Os caminhos da pasta, base, executáveis e estado ficam em `.automation/config.json`, ignorado pelo Git. Dados de alunos permanecem locais. `.automation/state/health.json` informa a última verificação; `current.json` aponta a versão validada; `releases/` mantém os snapshots; `alertas-pendentes.json` contém somente séries em revisão.

Reprocessar um arquivo idêntico não altera metas. Uma mudança na base de metas exige revisão explícita. Pisos da nova base não diminuem. Não há alerta de viabilidade do preço na interface, conforme decisão do usuário.

## Publicação
Durante a validação da interface integrada, `publish_enabled` e `auto_merge` permanecem falsos. O monitor atualiza o aplicativo local, mas não altera produção.

Após aprovação do rollout, o exportador usa checkout próprio, atualiza somente `boletins.json` e `boletins.js`, cria PR e exige CI `validate` aprovado. Confere origem Git, base master, repositório do PR, allowlist de arquivos, correspondência JSON/JS e preservação dos pisos antes de merge. Não há deploy direto. Vercel publica por integração Git após merge.

O caminho de publicação foi implementado, mas não foi exercitado com merge em produção nesta entrega. A validação de rede/CI é feita no PR de integração, e o fluxo periódico de dados só pode ser ativado depois que esse código entrar em master.

## E-mail
Não ativo. Vercel Marketplace oferece Resend e exige aceite de termos na conta Raiz antes de concluir instalação. A flag de revisão e a lista local de séries continuam sendo calculadas. Essa lista não equivale a e-mail enviado. Configuração do remetente, deduplicação de envios e teste de entrega dependem do serviço real.

## Evidências
- Base de 01/10/2026: 70 grupos, 5 unidades, 323 elegíveis (316 pré-matriculados e 7 matriculados).
- 4 testes Node de proposta e 11 testes Python passaram.
- Smoke com fonte real em diretório privado: carga, repetição, recuperação de artefatos, recuperação da fila, bloqueio de mudança da base e preservação após build inválido.
- Navegador: 70 séries, limite exato e um centavo abaixo, navegação entre páginas e mobile de 390px.
- Build, sintaxe, lint e auditoria de dependências passaram.
