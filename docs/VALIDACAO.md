# Validação — Apogeu, 30/09/2026

- Ficha de 30/09/2026: 397 vínculos de captação; 33 em cursos sem meta; 45 sem desconto efetivo de escolaridade; 3 sem financeiro completo; 316 elegíveis.
- Elegíveis: 307 pré-matriculados e 9 matriculados. Nenhum aluno individual é incluído no artefato público.
- 70 metas por escola/série; 80 preços; 70 ofertas de preço correspondidas (inclui PV em dois turnos). Berçário sem preço cheio consta na aba de metas, sem preço inventado.
- MD e escolaridade são serviços separados nesta ficha. Realizado = soma líquida de ambos /12. Reservas e outras receitas não compõem o ticket.
- Não houve financeiro ambíguo nem parcelas duplicadas na carga. Bolsa zero é verificada na escolaridade; material sem bolsa não exclui aluno que possui bolsa na mensalidade. Campo ausente não equivale a zero.
- Nenhuma série atingiu o limite de revisão de 30% na ficha atual. Teste numérico do caso real QI Valqueire verifica o caminho de alerta: R$ 1.906,00, limite R$ 1.830,25, horizonte 8.
- Alvos arredondados para cima no centavo, depois dos cálculos em precisão decimal, para respeitar o piso. Meta-base e realizado exibidos com duas casas.
- Testes Python: recuperação, manutenção do novo piso, idempotência matemática, ausência de alunos, quantidade zero e metas inválidas.
- JavaScript: sintaxe, dados carregados, equivalência de cursos, ausência de meta, sete bolsões sem datas, comparação com os pisos e ausência de campos pessoais no agregado.
- Build em dist publica somente index.html, dados.js, boletins.js e metas.js.
- Browser local: aba, filtros, cursos livres, cálculo de bolsa de 50%, layout 390 px sem overflow do corpo e nenhuma exceção JavaScript nas interações testadas.
- Varredura final no browser: 70 opções de negociação nas cinco unidades, desconto de 75%, alvo e recomendação presentes, sem NaN/undefined ou exceções. Filtro de alertas vazio consistente com a carga; Berçário presente em EI da Global Ferreira Guimarães.
- Importação é local por comando explícito. Monitoramento automático e envio de e-mail não estão ativos nesta entrega.
