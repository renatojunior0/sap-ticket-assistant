"""Interface de demonstração. Uso: streamlit run app/streamlit_app.py"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from assistant import config  # noqa: E402
from assistant.pipeline import analyze  # noqa: E402
from assistant.schemas import FinalResponse  # noqa: E402

STATUS_STYLE = {
    "RESPONDIDO": ("#1B7F3B", "Respondido"),
    "AGUARDANDO_INFORMACOES": ("#B8860B", "Aguardando informações"),
    "ESCALADO_HUMANO": ("#B23A3A", "Escalado para humano"),
    "FORA_ESCOPO": ("#5A6472", "Fora de escopo"),
}
CONFIDENCE_BANDS = [(0.75, "#1B7F3B", "alta"), (0.50, "#B8860B", "média"), (0.0, "#B23A3A", "baixa")]
NEUTRAL = "#5A6472"


def badge(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:4px 12px;border-radius:4px;'
        f'font-weight:600;font-size:0.85rem;letter-spacing:0.02em;white-space:nowrap">{text}</span>'
    )


def confidence_badge(value: float, has_analysis: bool) -> str:
    if not has_analysis:
        return badge("CONFIANÇA N/A", NEUTRAL)
    color, label = next((c, l) for threshold, c, l in CONFIDENCE_BANDS if value >= threshold)
    return badge(f"CONFIANÇA {label.upper()} {value:.2f}", color)


def render_header(result: FinalResponse, ticket_id: str) -> None:
    color, label = STATUS_STYLE[result.status.value]
    cols = st.columns([1.3, 1.5, 1.8, 1])
    cols[0].markdown(badge(label.upper(), color), unsafe_allow_html=True)
    cols[1].markdown(confidence_badge(result.confianca, result.analysis is not None), unsafe_allow_html=True)
    cols[2].markdown(
        badge("REQUER AUTORIZAÇÃO HUMANA", "#B23A3A") if result.requer_humano else badge("SEM AÇÃO CRÍTICA", "#1B7F3B"),
        unsafe_allow_html=True,
    )
    cols[3].caption(f"{ticket_id} | {result.latencia_ms / 1000:.1f} s")
    st.caption(f"Processo: {result.triage.processo} | Módulo: {result.triage.modulo} | {result.triage.resumo}")


def render_triage(result: FinalResponse) -> None:
    triage = result.triage
    cols = st.columns(3)
    cols[0].markdown("**Transações**\n\n" + (", ".join(f"`{t}`" for t in triage.transacoes) or "nenhuma"))
    cols[1].markdown("**Mensagens de erro**\n\n" + (", ".join(f"`{m}`" for m in triage.mensagens_erro) or "nenhuma"))
    cols[2].markdown("**Documentos**\n\n" + (", ".join(f"`{d}`" for d in triage.numeros_documento) or "nenhum"))
    if triage.fora_escopo:
        st.warning(f"Fora de escopo: {triage.motivo_fora_escopo or 'sem motivo informado'}")
    if not triage.completo:
        st.markdown("**Informações faltantes:** " + "; ".join(triage.informacoes_faltantes))
        for question in triage.perguntas_ao_usuario:
            st.markdown(f"- {question}")


def render_analysis(result: FinalResponse) -> None:
    analysis = result.analysis
    if analysis is None:
        st.info("Sem análise: o chamado não chegou à etapa de geração.")
        return
    st.markdown(f"**Diagnóstico:** {analysis.diagnostico}")
    left, right = st.columns(2)
    with left:
        st.markdown("**Causas prováveis**")
        for causa in analysis.causas:
            st.markdown(f"- [{causa.probabilidade}] {causa.descricao} — fontes: {', '.join(causa.fontes) or 'sem fonte'}")
    with right:
        st.markdown("**Verificações somente leitura**")
        for check in analysis.verificacoes_somente_leitura:
            st.markdown(f"- `{check.transacao or '—'}` {check.descricao}")
    if analysis.lacunas:
        st.warning("Lacunas da base: " + "; ".join(analysis.lacunas))


def render_human_actions(result: FinalResponse) -> None:
    if result.motivos_humano:
        st.error("Motivos para validação humana:\n" + "\n".join(f"- {m}" for m in result.motivos_humano))
    actions = result.analysis.acoes_requerem_autorizacao if result.analysis else []
    if not actions:
        st.caption("Nenhuma ação crítica identificada.")
        return
    st.dataframe(
        [{"Ação": a.descricao, "Risco": a.motivo_risco, "Responsável sugerido": a.responsavel_sugerido} for a in actions],
        hide_index=True,
        use_container_width=True,
    )


def render_sources(result: FinalResponse) -> None:
    if not result.fontes:
        st.caption("Nenhuma fonte consultada.")
        return
    st.dataframe(
        [{"Score": round(s.score, 3), "ID": s.id, "Título": s.titulo, "Seção": s.secao} for s in result.fontes],
        hide_index=True,
        use_container_width=True,
    )


def load_tickets() -> dict[str, dict]:
    tickets = json.loads(config.TICKETS_PATH.read_text(encoding="utf-8"))
    return {f"{t['id']} — {t.get('titulo', t.get('texto', ''))[:60]}": t for t in tickets}


st.set_page_config(page_title="Assistente de Chamados SAP MM", layout="wide")
st.title("Assistente Inteligente para Análise de Chamados SAP MM")
st.caption("A IA recomenda e fundamenta. Ações que alteram dados no SAP dependem de autorização humana.")

with st.sidebar:
    st.subheader("Configuração")
    st.markdown(f"**Provedor:** `{config.LLM_PROVIDER}`  \n**Modelo:** `{config.LLM_MODEL}`")
    st.markdown(f"**Embeddings:** `{config.EMBEDDING_MODEL}`  \n**Score mínimo:** `{config.RETRIEVAL_MIN_SCORE}`")
    options = load_tickets()
    choice = st.selectbox("Chamado de exemplo", ["(digitar manualmente)", *options])

selected = options.get(choice)
ticket_text = st.text_area("Texto do chamado", value=selected["texto"] if selected else "", height=140)
ticket_id = selected["id"] if selected else "ADHOC"

if st.button("Analisar chamado", type="primary", disabled=not ticket_text.strip()):
    with st.spinner("Triagem, ontologia, RAG híbrido, consulta SAP simulada, análise e política HITL..."):
        try:
            result = analyze(ticket_text, ticket_id)
        except Exception as exc:
            st.error(f"Falha no pipeline: {type(exc).__name__}: {str(exc)[:300]}")
            st.stop()

    render_header(result, ticket_id)
    tabs = st.tabs(["Resposta ao usuário", "Triagem", "Causas e verificações", "Ações humanas", "Fontes", "Dados SAP", "Auditoria"])
    with tabs[0]:
        st.markdown(result.mensagem_ao_usuario or "_Sem mensagem gerada._")
    with tabs[1]:
        render_triage(result)
    with tabs[2]:
        render_analysis(result)
    with tabs[3]:
        render_human_actions(result)
    with tabs[4]:
        render_sources(result)
    with tabs[5]:
        st.json(result.dados_sap_consultados or {"info": "nenhum documento consultado"})
    with tabs[6]:
        st.json(result.model_dump(mode="json"))
        st.caption(f"Registro gravado em {config.AUDIT_PATH.relative_to(config.ROOT)}")