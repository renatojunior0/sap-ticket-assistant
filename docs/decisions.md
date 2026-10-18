# Decisões de projeto

| Decisão | Alternativas consideradas | Justificativa |
|---|---|---|
| Módulo MM, processo Procure-to-Pay | SD, FI | Área de experiência do autor (S/4HANA, TAXBRA, estratégia de liberação, IDoc). Permite julgar a qualidade da resposta do LLM, não apenas gerá-la. |
| Pipeline determinístico com LLM em dois pontos (triagem e análise) | Agente autônomo com tools | O fluxo de suporte é conhecido e sequencial. Pipeline é auditável, previsível e barato. Agente só faria sentido para consulta multi-tool ao SAP, que aqui é simulada. |
| Ontologia MM em YAML (processos, transações, mensagens, ações críticas, fora de escopo) | Apenas prompt; OWL/RDF | Dá vocabulário controlado ao LLM e regras determinísticas à policy. Legível por consultor funcional; OWL seria custo sem ganho no protótipo. |
| RAG híbrido: BM25 + embeddings multilíngues + fusão RRF + boost pela triagem | Só embeddings | Códigos SAP (ME21N, M7053, J_1BTXIC1) são tokens exatos onde BM25 vence; linguagem natural do usuário pede embeddings. O boost por processo/transação detectado na triagem reduz ruído entre artigos vizinhos. |
| Duas camadas de conhecimento: 10 artigos curados + 21 documentos de referência | Só PDFs | Artigo curado tem estrutura sintoma, causa, verificação, ação, autorização humana, que vira resposta acionável. Documentos dão profundidade e citação por página (ex.: T09 cita SAP Localização BR_MM p. 191). |
| Saída estruturada validada por Pydantic | Texto livre | `causas`, `verificacoes_somente_leitura` e `acoes_requerem_autorizacao` são campos separados pelo schema. A separação IA versus humano é estrutural, não depende do prompt obedecer. |
| Validação de citações contra o contexto recuperado | Confiar na citação do LLM | Fonte citada que não existe no contexto zera a causa e, sem causa fundamentada, o caso escala. Na rodada 17:39 isso derrubou T03 e T09 para ESCALADO_HUMANO: o guardrail funcionou antes do ajuste de prompt. |
| Confiança composta: 0.5 retrieval + 0.3 completude do chamado + 0.2 autoavaliação | Só autoavaliação do LLM | Autoavaliação é otimista. Score de retrieval é evidência objetiva; completude vem da triagem. |
| Regras HITL independentes do score de confiança | Threshold único | T11 chega a 0.958 e mesmo assim escala: customizing (SPRO/OMW0) é decisão humana por definição, não por incerteza. |
| Groq com openai/gpt-oss-120b via API OpenAI-compatible | OpenAI, Anthropic, Gemini | Gratuito, rápido e trocável por `.env` (Gemini e Ollama já configurados). Provedor não é decisão arquitetural. |
| Embeddings locais (paraphrase-multilingual-MiniLM-L12-v2) | Embeddings via API | Sem custo, sem envio de documentos a terceiros, funciona offline após cache. |
| Streamlit | Gradio, FastAPI + React | Python puro no mesmo processo do pipeline; o edital não avalia sofisticação visual. |
| SAP simulado (`sap_mock.py`) | Sem dados SAP | Mostra onde entraria OData/RFC e permite cruzar evidência com o chamado (T02: período aberto 010 versus solicitado 009). |
| Log de auditoria em JSONL | Banco de dados | Requisito mínimo do edital; append-only, legível, suficiente para métricas. |