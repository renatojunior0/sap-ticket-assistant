"""Executa run_tickets.py para cada provedor LLM e consolida as evidências."""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_tickets.py"
EVIDENCE_DIR = ROOT / "docs" / "evidence"
AUDIT_PATH = ROOT / "logs" / "audit.jsonl"
AUDIT_SAMPLE_PATH = ROOT / "logs" / "audit_sample.jsonl"
DEFAULT_PROVIDERS = ("gemini", "groq", "ollama")
RUNNER_OUTPUT_GLOB = "run_[0-9]*.json"


def run_provider(provider: str, stamp: str, ids: str | None) -> Path:
    """Roda o runner com um único provedor (sem fallback) e renomeia a saída."""
    before = set(EVIDENCE_DIR.glob(RUNNER_OUTPUT_GLOB))
    env = {**os.environ, "LLM_PROVIDER": provider, "LLM_FALLBACK_PROVIDER": ""}
    command = [sys.executable, str(RUNNER)] + (["--ids", ids] if ids else [])
    subprocess.run(command, env=env, cwd=ROOT)  # exit 1 = chamados com erro; ainda gera evidência

    created = sorted(set(EVIDENCE_DIR.glob(RUNNER_OUTPUT_GLOB)) - before)
    if not created:
        raise RuntimeError("o runner não gerou arquivo de evidência")

    source_json = created[-1]
    target_json = EVIDENCE_DIR / f"run_{provider}_{stamp}.json"
    source_md = source_json.with_suffix(".md")
    source_json.rename(target_json)
    if source_md.exists():
        source_md.rename(target_json.with_suffix(".md"))
    return target_json


def summarize(evidence_path: Path) -> dict:
    runs = json.loads(evidence_path.read_text(encoding="utf-8"))
    tickets = {}
    for run in runs:
        result = run.get("resultado") or {}
        tickets[run["ticket_id"]] = {
            "esperado": run.get("cenario_esperado"),
            "status": result.get("status"),
            "confianca": result.get("confianca"),
            "requer_humano": result.get("requer_humano"),
            "fontes": len(result.get("fontes") or []),
            "latencia_ms": result.get("latencia_ms"),
            "erro": run.get("erro"),
        }
    return {
        "arquivo": evidence_path.name,
        "total": len(runs),
        "com_erro": sum(1 for t in tickets.values() if t["erro"]),
        "tickets": tickets,
    }


def write_audit_sample(started_at: datetime) -> int:
    """Uma entrada de auditoria por provedor, apenas desta execução."""
    if not AUDIT_PATH.exists():
        return 0
    picked: dict[str, str] = {}
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if datetime.fromisoformat(entry["timestamp"]) >= started_at:
            picked.setdefault(entry["provider"], line)
    if picked:
        AUDIT_SAMPLE_PATH.write_text("\n".join(picked.values()) + "\n", encoding="utf-8")
    return len(picked)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", default=",".join(DEFAULT_PROVIDERS))
    parser.add_argument("--ids", help="IDs de chamados separados por vírgula; padrão: todos")
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    matrix: dict[str, dict] = {}
    failed: list[str] = []

    for provider in (p.strip().lower() for p in args.providers.split(",")):
        print(f"\n[+] Provedor: {provider.upper()}")
        try:
            matrix[provider] = summarize(run_provider(provider, stamp, args.ids))
        except Exception as error:
            failed.append(provider)
            print(f"[-] {provider} falhou: {type(error).__name__}: {error}")

    if matrix:
        matrix_path = EVIDENCE_DIR / f"comparison_matrix_{stamp}.json"
        matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nMatriz: {matrix_path.relative_to(ROOT)}")
        for provider, data in matrix.items():
            print(f"  {provider}: {data['total']} chamados, {data['com_erro']} com erro")

    print(f"Amostra de auditoria: {write_audit_sample(started_at)} entrada(s) em logs/audit_sample.jsonl")
    if failed:
        print(f"[!] Sem evidência para: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
