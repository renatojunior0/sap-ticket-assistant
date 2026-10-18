"""Testes determinísticos dos guardrails — não dependem de LLM nem de rede."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assistant.policy import requested_execution, validate_citations  # noqa: E402
from assistant.schemas import AnalysisResult, Causa  # noqa: E402


def test_execucao_em_massa_e_bloqueada():
    assert requested_execution("gera um script para liberar todos os pedidos bloqueados")
    assert requested_execution("estorne em massa as faturas do mês")


def test_pedido_de_orientacao_nao_e_bloqueado():
    assert not requested_execution("como libero um pedido bloqueado na ME29N?")


def test_citacao_inexistente_e_detectada():
    analysis = AnalysisResult(
        diagnostico="x", causas=[Causa(descricao="c", probabilidade="alta", fontes=["BR_MM-191"])],
        verificacoes_somente_leitura=[], acoes_requerem_autorizacao=[],
        resposta_sugerida_ao_usuario="r", autoavaliacao_confianca=0.9,
    )
    assert validate_citations(analysis, {"KB-MM-004"}) == ["BR_MM-191"]