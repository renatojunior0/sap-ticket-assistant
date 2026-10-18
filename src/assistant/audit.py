import json
from datetime import datetime, timezone

from . import config
from .schemas import FinalResponse


def record(ticket_text: str, response: FinalResponse, retrieved: list[dict]) -> None:
    config.AUDIT_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": response.ticket_id,
        "provider": config.LLM_PROVIDER,
        "model": config.LLM_MODEL,
        "request": ticket_text,
        "status": response.status.value,
        "confianca": response.confianca,
        "requer_humano": response.requer_humano,
        "motivos_humano": response.motivos_humano,
        "fontes": [source.model_dump() for source in response.fontes],
        "chunks_recuperados": [{"id": r["chunk"].id, "score": r["score"]} for r in retrieved],
        "triage": response.triage.model_dump(),
        "analysis": response.analysis.model_dump() if response.analysis else None,
        "latencia_ms": response.latencia_ms,
    }
    with open(config.AUDIT_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
