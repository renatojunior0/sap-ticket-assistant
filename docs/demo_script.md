# Roteiro de demonstração (20 minutos)

Preparação: Streamlit aberto com embeddings em cache, `logs/audit.jsonl` aberto no editor, README com o diagrama visível, relatório `docs/evidence/run_20261016_175421.md` aberto.

| Minuto | Bloco | O que mostrar e dizer |
|---|---|---|
| 0 a 2 | Atividade transformada | Consultor hoje lê o chamado, identifica processo, pesquisa documentação, verifica no SAP e redige. 15 a 40 minutos por chamado, dependente da experiência individual. O assistente faz triagem, pesquisa e rascunho fundamentado; o consultor vira revisor e aprovador. |
| 2 a 4 | Por que GenAI e arquitetura | Entrada é texto ambíguo em linguagem natural: LLM. Saída precisa ser rastreável: RAG, ontologia e policy. LLM em apenas dois pontos; o restante é determinístico. Mostrar o diagrama. |
| 4 a 7 | Base de conhecimento e ontologia | Abrir `KB-MM-004.md` (estrutura sintoma, causa, verificação, ação, autorização humana). Abrir `mm_ontology.yaml` (processos, transações, ações críticas, módulos fora de escopo). Números: 92 transações, 417 chunks, 30 documentos no manifesto, 21 indexados. |
| 7 a 11 | Cenário de sucesso: T02 | Rodar ao vivo. Triagem detecta MIGO, M7053, pedido. SAP simulado mostra período aberto 010 versus solicitado 009. Causa cita KB-MM-004. Verificações somente leitura (MMRV, OB52 exibir). Ações humanas separadas: abrir período, responsável Controller. Confiança 0.99 e mesmo assim `requer_humano = true`. Mostrar a linha gravada no audit. |
| 11 a 14 | Exceções 1 e 2: T05 e T08 | T05 ("não consigo criar pedido, erro de autorização") retorna AGUARDANDO_INFORMACOES com perguntas objetivas: transação, print da SU53, organização de compras. Explicar a regra de completude. T08 (script para liberar todos os pedidos) retorna FORA_ESCOPO em 2 s, sem chamar o LLM de análise. Frase-chave: não existe ferramenta de escrita; isso é arquitetura, não prompt. |
| 14 a 17 | Exceção 3 e anti-alucinação: T11 | Split valuation: confiança 0.958, fonte KB-MM-010, status ESCALADO_HUMANO por regra de customizing. Abrir `policy.py` em `validate_citations` e `human_review_reasons`. Contar a rodada 17:39: T03 e T09 escalaram por citação inválida; o guardrail agiu antes da correção do prompt. |
| 17 a 19 | Dados reais, métricas, próximos passos | OData read-only, principal propagation, ações viram aprovação em workflow. Tabela de métricas de `risks.md`. Três próximos passos. |
| 19 a 20 | Fechamento | Não é um chatbot: é um fluxo auditável em que a IA pesquisa e redige e o humano decide. Abrir para perguntas. |

## Perguntas e respostas

- Por que não usar agente? O fluxo é conhecido e sequencial; agente adicionaria imprevisibilidade sem ganho. Faria sentido apenas na consulta ao SAP com múltiplas tools.
- E se o LLM mudar o formato da resposta? Pydantic valida; falha gera retry e, persistindo, escalação.
- Como garante que não executa nada? Não existe tool de escrita e `requested_execution` bloqueia antes do LLM.
- Custo? Duas chamadas de LLM por chamado, embeddings locais, Groq gratuito no protótipo.
- Ontologia versus prompt? Prompt é probabilístico; a ontologia alimenta regras determinísticas da policy e o boost do retriever.
- Por que a confiança de T04 é alta se o usuário pede algo que não pode? A confiança mede fundamentação da resposta, não a permissão da ação; a permissão é tratada pelas regras HITL.