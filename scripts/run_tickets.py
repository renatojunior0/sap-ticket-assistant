"""Roda todos os chamados de data/tickets/tickets.json pelo pipeline e gera evidências em docs/evidence/.
Uso: python scripts/run_tickets.py [--ids T01,T07]"""
import argparse
import json
import sys
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assistant import config  # noqa: E402
from assistant.pipeline import analyze  # noqa: E402

EVIDENCE_DIR = config.ROOT / "docs" / "evidence"


def to_dict(result) -> dict:
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    if is_dataclass(result):
        return asdict(result)
    return dict(result)


def ticket_text(ticket: dict) -> str:
    parts = [ticket.get(k, "") for k in ("titulo", "descricao") if ticket.get(k)]
    return "\n".join(parts) or ticket.get("texto", "")


def run_one(ticket: dict) -> dict:
    started = time.perf_counter()
    try:
        payload = to_dict(analyze(ticket_text(ticket)))
        error = None
    except Exception as exc:
        payload, error = {}, f"{type(exc).__name__}: {str(exc)[:300]}"
    return {
        "ticket_id": ticket.get("id"),
        "titulo": ticket.get("titulo"),
        "cenario_esperado": ticket.get("cenario_esperado") or ticket.get("esperado"),
        "duracao_s": round(time.perf_counter() - started, 2),
        "erro": error,
        "resultado": payload,
    }


def find_field(data, *candidates):
    """Busca a primeira chave existente em qualquer nível do dicionário."""
    if isinstance(data, dict):
        for key in candidates:
            if data.get(key) not in (None, "", []):
                return data[key]
        for value in data.values():
            found = find_field(value, *candidates)
            if found is not None:
                return found
    return None


def summarize(run: dict) -> dict:
    result = run["resultado"]
    sources = find_field(result, "sources", "fontes") or []
    return {
        "id": run["ticket_id"],
        "status": find_field(result, "status"),
        "processo": find_field(result, "processo", "process", "processo_sap", "sap_process"),
        "confianca": find_field(result, "confidence", "confianca", "confidence_score"),
        "fontes": len(sources),
        "revisao_humana": find_field(result, "requires_human_review", "revisao_humana", "human_review", "needs_human"),
        "duracao_s": run["duracao_s"],
        "erro": run["erro"],
    }



def write_report(runs: list[dict], stamp: str) -> Path:
    rows = [summarize(r) for r in runs]
    header = "| ID | Status | Processo | Confiança | Fontes | HITL | Tempo (s) | Erro |\n|---|---|---|---|---|---|---|---|"
    body = "\n".join(
        f"| {r['id']} | {r['status']} | {r['processo']} | {r['confianca']} | {r['fontes']} | {r['revisao_humana']} | {r['duracao_s']} | {r['erro'] or '-'} |"
        for r in rows
    )
    details = "\n\n".join(
        f"### {r['ticket_id']} — {r['titulo']}\n\n**Cenário esperado:** {r['cenario_esperado']}\n\n```json\n"
        f"{json.dumps(r['resultado'], ensure_ascii=False, indent=2)[:6000]}\n```"
        for r in runs
    )
    report = (
        f"# Evidências de teste — {stamp}\n\n"
        f"Provedor: `{config.LLM_PROVIDER}` · Modelo: `{config.LLM_MODEL}` · Embeddings: `{config.EMBEDDING_MODEL}` · TOP_K={config.TOP_K}\n\n"
        f"## Resumo\n\n{header}\n{body}\n\n## Detalhes por chamado\n\n{details}\n"
    )
    path = EVIDENCE_DIR / f"run_{stamp}.md"
    path.write_text(report, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="IDs separados por vírgula; padrão: todos")
    args = parser.parse_args()

    tickets = json.loads(config.TICKETS_PATH.read_text(encoding="utf-8"))
    if isinstance(tickets, dict):
        tickets = tickets.get("tickets", list(tickets.values()))
    if args.ids:
        wanted = set(args.ids.split(","))
        tickets = [t for t in tickets if t.get("id") in wanted]

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs = [run_one(t) for t in tickets]

    (EVIDENCE_DIR / f"run_{stamp}.json").write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")
    report = write_report(runs, stamp)

    for row in map(summarize, runs):
        print(row)
    failures = sum(1 for r in runs if r["erro"])
    print(f"\n{len(runs)} chamados | {failures} erros | relatório: {report.relative_to(config.ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())