# Integração da precificação e atualização local

## Escopo aprovado em 05/10/2026
Integrar o rascunho à calculadora existente, com páginas de tickets e de propostas, e processar automaticamente fichas Apogeu na pasta local. Não adicionar aviso de viabilidade. Não publicar em produção antes da validação da interface integrada.

## Decisões
- Manter HTML/JS estático, Python/openpyxl e pipeline GitHub/Vercel existentes, sem novas dependências.
- Duas URLs: tickets.html e calculadora.html. Unidade preservada nos links.
- Todas as 70 metas são acessíveis; entrada por ticket total permite Berçário sem inventar preço cheio. MD vem da meta validada.
- Proposta final inclui MD; mensalidade = total - MD/12. Sem desconto adicional automático de irmão sobre o total informado.
- Comparação monetária em centavos com ticket_alvo. Exibir Dentro/Fora, diferença, referência e data da ficha. Igualdade conta como Dentro.
- Tabela: série, alunos/meta, ticket meta, ticket médio atual, ticket projetado e situação. Sem colunas internas de horizonte/limite.
- Regra permanece max(base*1.10, recuperação, anterior); não aplicar outra margem à recuperação. Alerta interno continua base*1.30.

## Monitor local
- Configuração privada com caminhos absolutos; nenhum XLSX ou identificador de aluno enviado ao GitHub.
- Detectar arquivos pelo padrão e pela data do nome, ignorar arquivos temporários e exigir estabilidade antes/depois da leitura.
- Mesmo hash não gera nova carga. Ficha anterior nunca substitui a atual. Base diferente exige revisão.
- Lock por processo no Windows impede duas execuções simultâneas; estado/erros locais sem PII.
- Staging privado: importar, validar invariantes e compatibilidade, construir publicação; só promover carga válida. Falha mantém anterior.
- Guardar snapshots para recuperar pisos; registro atômico da carga ativa. Distribuição pública usa somente agregados.
- Rotina periódica local: máquina ligada, sessão disponível e acesso à pasta. Retentativa na próxima execução; não alterar fontes.
- Exportação Git em checkout isolado: apenas agregados em branch e PR, com CI antes de merge. Publicação automática permanece desligada até aprovação do rollout.
- Alertas por série devem ser deduplicados por entrada em revisão ou aumento do alvo; envio depende de serviço real configurado.

## Testes e aceitação
- Proposta abaixo/exatamente/acima; centavo limítrofe; vazio/negativo/abaixo MD; sem série.
- Cobertura real de todas unidades/metas; mesma referência na tabela e calculadora; navegação/móvel.
- Nova ficha, repetição, falha, arquivo em escrita, anterior, alteração de base, lock e preservação de piso.
- Reimportação real 01/10 e comparação com estado 30/09; testes do motor existente preservados.
- PR e checks. Produção depende da validação da prévia integrada.

## Referências locais
PRD.md e SPEC.md fornecem regras anteriores; este documento prevalece para interface e automação. Catálogo de design e KB TOTVS nos caminhos indicados pela skill não existem nesta máquina; preservar interface Apogeu aprovada e contrato XLSX já validado.
