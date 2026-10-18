"""Gera data/kb_manifest.yaml: inventário dos documentos da base de conhecimento.
Rode após ingest_kb.py. Uso: python scripts/build_kb_manifest.py
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf
import yaml

from build_ontology import process_for
from ingest_kb import EXCLUDE_PATTERNS, OUTPUT as CHUNKS, RAW_DIR

ROOT = RAW_DIR.parents[1]
MANIFEST = ROOT / "data" / "kb_manifest.yaml"

# (regex no nome, origem, tipo, processos). processos=None -> inferir pelo código de transação no nome.
SOURCE_RULES = [
    (r"^\d{3} ", "Ka Solution — SAP S/4HANA MM Academy (apostila passo a passo)", "passo_a_passo", None),
    (r"^EXFOCA_COMPRAS", "Exercício prático autoral", "exercicio", ["requisicao_compra", "pedido_compra"]),
    (r"^EXFOCA_IMPOSTOS", "Exercício prático autoral", "exercicio", ["localizacao_brasil", "verificacao_fatura"]),
    (r"^EXFOCA_MOV", "Exercício prático autoral", "exercicio", ["entrada_mercadoria"]),
    (r"^EX_ESTRUT", "Exercício prático autoral", "exercicio", ["dados_mestres"]),
    (r"Localiza", "Material de apoio Localização Brasil (TAXBRA / NF)", "referencia", ["localizacao_brasil", "verificacao_fatura"]),
    (r"^MM_CONTABILIZA", "Nota técnica autoral", "referencia", ["entrada_mercadoria", "verificacao_fatura"]),
    (r"^MM_SIEC", "Documentação funcional S/4HANA", "referencia", ["dados_mestres", "pedido_compra", "entrada_mercadoria"]),
    (r"^Movimentos_SAP", "Referência de tipos de movimento", "referencia", ["entrada_mercadoria"]),
    (r"^SAP MM\.pdf$", "Apostila geral SAP MM", "referencia", ["dados_mestres", "pedido_compra", "entrada_mercadoria"]),
    (r"^SAP WM", "Apostila SAP WM", "referencia", []),
    (r"^(TS45|S99513)", "SAP Education — material licenciado (exercícios, EN)", "licenciado", []),
    (r"^Transa", "Planilha corporativa de transações (todos os módulos)", "ontologia", []),
]
EXCLUSION_REASONS = {
    "TS450": "licenciado SAP Education, inglês, formato exercício — dilui o retriever",
    "TS452": "licenciado SAP Education, inglês, formato exercício — dilui o retriever",
    "S99513": "licenciado, formato exercício — dilui o retriever",
    "SAP WM": "módulo fora do escopo (WM)",
    "Transações sap": "consumida por build_ontology.py (vira catálogo/ontologia, não chunk)",
}


def classify(name: str) -> dict:
    origin, kind, processes = next(((o, k, p) for rx, o, k, p in SOURCE_RULES if re.search(rx, name, re.I)), ("Não classificado", "referencia", []))
    if processes is None:  # apostila de transação: ex. '014 MIGO.pdf' -> entrada_mercadoria
        codes = re.findall(r"\b[A-Z]{2,4}\d{1,2}[A-Z]?\b", name.upper())
        processes = sorted({p for c in codes if (p := process_for(c))}) or ["visao_geral_p2p"]
    return {"origem": origin, "tipo": kind, "processos": processes}


def pages_of(path: Path) -> int | None:
    try:
        return len(pymupdf.open(path)) if path.suffix.lower() == ".pdf" else None
    except Exception:
        return None


def main() -> None:
    chunks, modes = Counter(), {}
    if CHUNKS.exists():
        for line in CHUNKS.open(encoding="utf-8"):
            record = json.loads(line)
            chunks[record["source"]] += 1
            modes[record["source"]] = record["mode"]

    documents = []
    for path in sorted(p for p in RAW_DIR.iterdir() if p.suffix.lower() in {".pdf", ".docx", ".xlsx", ".xls"}):
        excluded_by = next((p for p in EXCLUDE_PATTERNS if p.lower() in path.name.lower()), None)
        documents.append({
            "arquivo": path.name, "formato": path.suffix.lstrip(".").lower(), "tamanho_kb": round(path.stat().st_size / 1024),
            "paginas": pages_of(path), **classify(path.name),
            "status": "excluido" if excluded_by else ("indexado" if chunks[path.name] else "sem_texto"),
            "motivo_exclusao": EXCLUSION_REASONS.get(excluded_by) if excluded_by else None,
            "extracao": modes.get(path.name), "chunks": chunks[path.name],
        })

    by_process = defaultdict(int)
    for doc in documents:
        if doc["status"] == "indexado":
            for process in doc["processos"]:
                by_process[process] += doc["chunks"]
    status = Counter(d["status"] for d in documents)
    manifest = {
        "resumo": {"documentos": len(documents), **status, "chunks_indexados": sum(chunks.values()),
                   "chunks_por_processo": dict(sorted(by_process.items())), "chunks_por_extracao": dict(Counter(modes.values()))},
        "documentos": documents,
    }
    MANIFEST.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    print(json.dumps(manifest["resumo"], ensure_ascii=False))
    print(f"-> {MANIFEST.relative_to(ROOT)}")
    
if __name__ == "__main__":
    main()
