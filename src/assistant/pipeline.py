import json
import time

from . import audit, config, ontology, policy, sap_mock
from .llm import chat_json
from .prompts import ANALYSIS_SYSTEM, TRIAGE_SYSTEM, build_analysis_user_prompt, build_triage_user_prompt
from .retriever import HybridRetriever, format_context
from .schemas import AnalysisResult, FinalResponse, SourceRef, Status, TriageResult

_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def _confidence_label(confidence: float) -> str:
    if confidence >= config.CONFIDENCE_HIGH:
        return "ALTA"
    return "MEDIA" if confidence >= config.CONFIDENCE_LOW else "BAIXA"


def _run_triage(ticket_text: str) -> TriageResult:
    triage = chat_json(TRIAGE_SYSTEM, build_triage_user_prompt(ticket_text, ontology.summary_for_prompt()), TriageResult)
    if triage.processo not in ontology.load_ontology()["processos"] and (inferred := ontology.infer_process(ticket_text)):
        triage.processo = inferred
    # Guardrails determinísticos (independem do LLM)
    forbidden = ontology.modules_mentioned(ticket_text) & set(ontology.load_ontology()["fora_escopo"]["modulos"])
    if forbidden:
        triage.fora_escopo, triage.motivo_fora_escopo = True, f"Transação de módulo fora de escopo ({', '.join(sorted(forbidden))})"
    if policy.requested_execution(ticket_text):
        triage.fora_escopo = True
        triage.motivo_fora_escopo = "Solicitação de execução de ação em massa/script: o assistente apenas orienta, não executa ações no SAP"
    if not triage.fora_escopo and not triage.completo and policy.is_analyzable(triage, ticket_text):
        triage.completo = True  # há evidência mínima: analisa e lista o que falta como verificação, em vez de bloquear
    return triage


def _escalate(response: FinalResponse, reasons: list[str], message: str) -> FinalResponse:
    response.status, response.requer_humano = Status.ESCALADO_HUMANO, True
    response.motivos_humano, response.mensagem_ao_usuario = reasons, message
    return response


def analyze(ticket_text: str, ticket_id: str = "ADHOC") -> FinalResponse:
    started = time.perf_counter()
    triage = _run_triage(ticket_text)
    response = FinalResponse(ticket_id=ticket_id, status=Status.RESPONDIDO, triage=triage)
    configuration_request = policy.requested_configuration(ticket_text)
    if configuration_request:
        triage.completo = True  # não pede "mensagem de erro" para pedido de configuração
    retrieved: list[dict] = []

    if triage.fora_escopo:
        response.status, response.requer_humano = Status.FORA_ESCOPO, False
        response.mensagem_ao_usuario = (
            "Este chamado está fora do escopo deste assistente (suporte funcional SAP MM, sem execução de ações). "
            f"Motivo: {triage.motivo_fora_escopo}. Encaminhe ao canal responsável."
        )
    elif not triage.completo:
        response.status, response.requer_humano = Status.AGUARDANDO_INFORMACOES, False
        questions = "\n".join(f"- {q}" for q in triage.perguntas_ao_usuario) or "- Descreva transação, mensagem de erro e documento envolvido."
        response.mensagem_ao_usuario = f"Para analisar seu chamado preciso de mais informações:\n{questions}"
    else:
        boost = set(triage.transacoes) | set(triage.mensagens_erro) | ontology.process_vocabulary(triage.processo)
        retrieved = get_retriever().search(f"{triage.resumo}\n{ticket_text}", boost_terms=boost, process=triage.processo)
        best_score = retrieved[0]["score"] if retrieved else 0.0
        response.fontes = [SourceRef(id=r["chunk"].doc_id, titulo=r["chunk"].titulo, secao=r["chunk"].secao, score=r["score"])
                           for r in retrieved]

        if best_score < config.RETRIEVAL_MIN_SCORE:
            response.confianca = policy.compute_confidence(best_score, triage, None)
            _escalate(response, [f"Melhor evidência ({best_score:.2f}) abaixo do mínimo ({config.RETRIEVAL_MIN_SCORE:.2f})"],
                      "Não encontrei evidência suficiente na base de conhecimento para orientar com segurança. "
                      "O chamado foi encaminhado a um consultor.")
        else:
            response.dados_sap_consultados = sap_mock.lookup_documents(triage.numeros_documento)
            if triage.processo == "entrada_mercadoria":
                response.dados_sap_consultados["periodos_contabeis"] = sap_mock.lookup_posting_period()

            analysis = chat_json(
                ANALYSIS_SYSTEM,
                build_analysis_user_prompt(ticket_text, triage.model_dump_json(indent=2), format_context(retrieved),
                                           json.dumps(response.dados_sap_consultados, ensure_ascii=False, indent=2)),
                AnalysisResult,
            )
            allowed_ids = {r["chunk"].doc_id for r in retrieved}
            invalid = policy.validate_citations(analysis, allowed_ids)
            response.analysis = analysis
            response.confianca = policy.compute_confidence(best_score, triage, analysis)
            reasons = policy.human_review_reasons(response.confianca, analysis, invalid, config.CONFIDENCE_LOW, configuration_request)
            response.requer_humano, response.motivos_humano = bool(reasons), reasons
            response.mensagem_ao_usuario = analysis.resposta_sugerida_ao_usuario
            if configuration_request or invalid or response.confianca < config.CONFIDENCE_LOW or not analysis.causas:
                response.status = Status.ESCALADO_HUMANO

    response.nivel_confianca = _confidence_label(response.confianca)
    response.latencia_ms = int((time.perf_counter() - started) * 1000)
    audit.record(ticket_text, response, retrieved)
    return response