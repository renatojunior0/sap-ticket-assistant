# Riscos, limitações e futuras melhorias

## Riscos e mitigações implementadas

| Risco | Mitigação |
|---|---|
| Alucinação de causas, transações ou tabelas | Somente fontes recuperadas entram no prompt; citações validadas contra o contexto; zero causas fundamentadas implica ESCALADO_HUMANO. |
| Resposta confiante porém errada | Confiança composta (retrieval + completude + autoavaliação) e regras de risco que escalam independentemente do score. |
| Execução indevida no SAP | Não existe ferramenta de escrita. Pedido de script ou alteração em massa (T08) vira FORA_ESCOPO por regra, antes de qualquer chamada ao LLM. |
| Resposta a assunto fora de MM (T07, HR) | Ontologia lista módulos fora de escopo; triagem encerra sem análise. |
| Chamado vago gerar resposta genérica (T05, T06) | Regra de completude: documento, ou mensagem de erro, ou transação + sintoma. Faltando, retorna perguntas objetivas. |
| Vazamento de dados para o provedor LLM | Protótipo usa dados fictícios. Em produção: LLM privado ou com DPA, mascaramento de PII e de números de documento antes do prompt. |
| Dependência de provedor | Interface OpenAI-compatible; troca por `.env` sem alterar código. |
| Deriva de versões entre módulos | `scripts/smoke_imports.py` valida símbolos de todos os módulos antes de subir a aplicação. |

## Limitações do protótipo

- 10 artigos curados cobrindo P2P; fora disso o retriever cai nos PDFs, com respostas menos acionáveis.
- SAP simulado: não há leitura real de EKKO, RBKP, MARD ou períodos (MMRV).
- 11 chamados sintéticos; não há métrica estatística de precisão.
- Latência de 2 a 42 s por chamado (média 18,7 s na rodada 17:54), dominada pelo LLM.
- Sem memória de conversa: o fluxo AGUARDANDO_INFORMACOES exige novo chamado com a resposta.
- Avaliação de qualidade foi manual, por leitura das respostas.

## Como acessar dados reais do SAP com segurança

1. Somente leitura, via OData (API_PURCHASEORDER_PROCESS_SRV, API_SUPPLIERINVOICE_PROCESS_SRV, API_MATERIAL_DOCUMENT_SRV) ou BAPIs de leitura. Nunca acesso direto a tabelas.
2. Usuário técnico com roles mínimas e propagação da identidade do solicitante (principal propagation), preservando SoD: o assistente nunca vê mais do que o usuário veria.
3. Allowlist de entidades e campos; mascaramento de campos sensíveis (CNPJ, dados bancários) antes de compor o prompt.
4. Toda ação de escrita (liberar pedido, abrir período, liberar fatura, estornar) sai do assistente como tarefa de aprovação em workflow (SAP Build Process Automation ou ITSM), com o responsável nomeado no artigo da KB.
5. Em S/4HANA, Joule e SAP AI Core mantêm o dado dentro do perímetro SAP; o assistente atuaria como orquestrador, não como repositório.
6. Log de auditoria com chamado, fontes, confiança, decisão e quem aprovou cada ação.

## Como medir redução de tempo, qualidade e produtividade

| Dimensão | Métrica | Fonte |
|---|---|---|
| Tempo | Tempo até primeira resposta e até resolução, antes e depois | ITSM versus `latencia_ms` do audit |
| Qualidade | Percentual de respostas aceitas sem edição; taxa de reabertura; nota do consultor revisor | Botão aceitar/editar na interface gravado no audit |
| Fundamentação | Percentual de respostas com pelo menos uma fonte válida; citações inválidas por 100 chamados | `logs/audit.jsonl` |
| Autonomia | Distribuição de status (RESPONDIDO, AGUARDANDO, FORA_ESCOPO, ESCALADO); precisão da escalação em revisão amostral | audit + revisão humana |
| Produtividade | Chamados por consultor por dia; horas economizadas = (tempo médio manual - tempo de revisão) x volume | ITSM + audit |

## Melhorias Futuras

1. Botão de feedback na interface alimentando um conjunto de avaliação.
2. Avaliação automatizada (RAGAS ou LLM-as-judge) sobre 50 ou mais chamados reais anonimizados.
3. Conector OData read-only substituindo `sap_mock.py`.
4. Mineração de chamados fechados para gerar novos artigos curados.
5. Memória de sessão para o fluxo AGUARDANDO_INFORMACOES seguido de reanálise.
6. Tracing e custo por chamado; cache de respostas para chamados semelhantes.