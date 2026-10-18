import streamlit as st

STATUS_STYLE = {
    "RESPONDIDO": ("#1B7F3B", "Respondido"),
    "AGUARDANDO_INFORMACOES": ("#B8860B", "Aguardando informações"),
    "ESCALADO_HUMANO": ("#B23A3A", "Escalado para humano"),
    "FORA_ESCOPO": ("#5A6472", "Fora de escopo"),
}
CONFIDENCE_BANDS = [(0.75, "#1B7F3B", "alta"), (0.50, "#B8860B", "média"), (0.0, "#B23A3A", "baixa")]


def _badge(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:4px 12px;border-radius:4px;'
        f'font-weight:600;font-size:0.85rem;letter-spacing:0.02em">{text}</span>'
    )


def status_badge(status: str) -> str:
    color, label = STATUS_STYLE.get(status, ("#5A6472", status))
    return _badge(label.upper(), color)


def confidence_badge(value: float | None) -> str:
    if value is None:
        return _badge("CONFIANÇA N/A", "#5A6472")
    color, label = next((c, l) for threshold, c, l in CONFIDENCE_BANDS if value >= threshold)
    return _badge(f"CONFIANÇA {label.upper()} {value:.2f}", color)


def human_badge(required: bool) -> str:
    return _badge("REQUER AUTORIZAÇÃO HUMANA" if required else "SEM AÇÃO CRÍTICA", "#B23A3A" if required else "#1B7F3B")


def header(result: dict) -> None:
    cols = st.columns([1.2, 1.4, 1.6, 1])
    cols[0].markdown(status_badge(result.get("status", "")), unsafe_allow_html=True)
    cols[1].markdown(confidence_badge(result.get("confianca")), unsafe_allow_html=True)
    cols[2].markdown(human_badge(bool(result.get("requer_humano"))), unsafe_allow_html=True)
    latency = result.get("latencia_ms")
    cols[3].caption(f"{latency / 1000:.1f} s" if latency else "")


def section(title: str, items, empty_text: str = "Nenhum item.") -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption(empty_text)
        return
    for item in items:
        st.markdown(f"- {item}" if isinstance(item, str) else f"- {format_item(item)}")


def format_item(item: dict) -> str:
    text = item.get("descricao") or item.get("texto") or item.get("acao") or item.get("causa") or str(item)
    extras = [f"`{item[k]}`" for k in ("transacao", "responsavel", "fonte") if item.get(k)]
    return f"{text} " + " ".join(extras) if extras else text


def sources_table(sources: list[dict]) -> None:
    st.markdown("**Fontes consultadas**")
    if not sources:
        st.caption("Nenhuma fonte utilizada.")
        return
    st.dataframe(
        [{"ID": s.get("id"), "Título": s.get("titulo"), "Seção": s.get("secao"), "Score": s.get("score")} for s in sources],
        hide_index=True,
        use_container_width=True,
    )