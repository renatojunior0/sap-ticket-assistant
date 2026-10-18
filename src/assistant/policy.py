import re

from .ontology import critical_actions
from .schemas import AnalysisResult, TriageResult

EXECUTION_PATTERNS = [
    r"\b(libere|libera|estorne|estorna|execute|executa|rode|roda|altere|altera)\b.*\b(todos|todas|em massa|script|automaticamente)\b",
    r"\bscript\b", r"\bem massa\b",
]
CONFIGURATION_PATTERNS = [r"\bspro\b", r"\bcustomiz", r"\bconfigurar\b", r"\bconfigura[çc][aã]o\b", r"\bimg\b", r"\bparametriza"]
TOKEN = re.compile(r"[a-z0-9]{3,}")


def detect_critical_intent(text: str) -> list[str]:
    lowered = text.lower()
    return [action for action in critical_actions() if action in lowered]


def requested_execution(text: str) -> bool:
    return any(re.search(p, text.lower()) for p in EXECUTION_PATTERNS)


def requested_configuration(text: str) -> bool:
    """Pedidos de customizing (SPRO) nunca são resolvidos pelo assistente: exigem change request e validação humana."""
    return any(re.search(p, text.lower()) for p in CONFIGURATION_PATTERNS)


def is_analyzable(triage: TriageResult, text: str) -> bool:
    """Completude por evidência mínima (OR), não por checklist (AND).
    Analisável se há documento OU mensagem de erro OU (transação + sintoma descrito)."""
    has_symptom = len(text.split()) >= 15
    return bool(triage.numeros_documento or triage.mensagens_erro or (triage.transacoes and has_symptom))


def _tokens(value: str) -> set[str]:
    return set(TOKEN.findall(value.lower()))


def normalize_citation(cited: str, allowed_ids: set[str]) -> str | None:
    """Mapeia citações 'livres' do LLM ('BR_MM-191', 'SAP MM.pdf p. 12') para o doc_id recuperado."""
    cited_tokens = _tokens(cited)
    best = max(allowed_ids, key=lambda a: len(_tokens(a) & cited_tokens), default=None)
    return best if best and (_tokens(best) & cited_tokens) else None


def validate_citations(analysis: AnalysisResult, allowed_ids: set[str]) -> list[str]:
    """Normaliza citações in-place e retorna as que não mapeiam a nenhuma fonte recuperada (indício de alucinação)."""
    invalid = []
    for item in [*analysis.causas, *analysis.verificacoes_somente_leitura]:
        normalized = []
        for source in item.fontes:
            match = source if source in allowed_ids else normalize_citation(source, allowed_ids)
            (normalized.append(match) if match else invalid.append(source))
        item.fontes = sorted(set(normalized))
    return sorted(set(invalid))


def compute_confidence(retrieval_score: float, triage: TriageResult, analysis: AnalysisResult | None) -> float:
    completeness = 1.0 if triage.completo else 0.3
    self_assessment = analysis.autoavaliacao_confianca if analysis else 0.0
    return round(0.5 * retrieval_score + 0.3 * completeness + 0.2 * self_assessment, 3)


def human_review_reasons(confidence: float, analysis: AnalysisResult | None, invalid_citations: list[str],
                         low_threshold: float, configuration_request: bool = False) -> list[str]:
    reasons = []
    if configuration_request:
        reasons.append("Solicitação de configuração (SPRO/customizing): exige change request, teste em QAS e aprovação — decisão humana obrigatória")
    if confidence < low_threshold:
        reasons.append(f"Confiança {confidence:.2f} abaixo do mínimo {low_threshold:.2f}")
    if invalid_citations:
        reasons.append(f"Fontes citadas inexistentes no contexto recuperado: {invalid_citations}")
    if analysis and analysis.acoes_requerem_autorizacao:
        reasons.append("Resolução depende de ação crítica que exige autorização humana")
    if analysis and not analysis.causas:
        reasons.append("Nenhuma causa fundamentada encontrada na base")
    return reasons