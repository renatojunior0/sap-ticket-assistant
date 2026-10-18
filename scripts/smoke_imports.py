"""Verifica se cada módulo importa e expõe os símbolos que o pipeline usa. Uso: python scripts/smoke_imports.py"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REQUIRED = {
    "assistant.config": ["ROOT", "KB_DIR", "CHUNKS_PATH", "MANIFEST_PATH", "ONTOLOGY_PATH", "TICKETS_PATH", "AUDIT_PATH",
                         "CACHE_DIR", "LLM_PROVIDER", "LLM_MODEL", "EMBEDDING_MODEL", "TOP_K", "RETRIEVAL_MIN_SCORE",
                         "CONFIDENCE_HIGH", "CONFIDENCE_LOW", "Settings", "load_settings", "list_chat_models"],
    "assistant.schemas": ["TriageResult", "AnalysisResult", "FinalResponse", "SourceRef", "Status"],
    "assistant.prompts": ["TRIAGE_SYSTEM", "ANALYSIS_SYSTEM", "build_triage_user_prompt", "build_analysis_user_prompt"],
    "assistant.llm": ["LLMClient", "chat_json"],
    "assistant.ontology": ["load_ontology", "summary_for_prompt", "infer_process", "modules_mentioned", "process_vocabulary"],
    "assistant.policy": ["requested_execution", "compute_confidence", "validate_citations", "human_review_reasons"],
    "assistant.sap_mock": ["lookup_documents", "lookup_posting_period"],
    "assistant.audit": ["record"],
    "assistant.ingest": ["Chunk", "load_chunks"],
    "assistant.retriever": ["HybridRetriever", "format_context"],
    "assistant.pipeline": ["analyze"],
}


def main() -> int:
    failures = []
    for module_name, symbols in REQUIRED.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as error:
            failures.append(f"{module_name}: falha ao importar -> {type(error).__name__}: {str(error)[:200]}")
            continue
        missing = [s for s in symbols if not hasattr(module, s)]
        if missing:
            failures.append(f"{module_name}: faltam {missing}")
        else:
            print(f"ok  {module_name}")

    if failures:
        print("\n".join(f"ERR {f}" for f in failures))
        return 1

    from assistant.ingest import load_chunks
    chunks = load_chunks()
    curated = sum(c.metadata.get("tipo") == "artigo_curado" for c in chunks)
    print(f"\nchunks: {len(chunks)} (artigos curados: {curated}, documentos: {len(chunks) - curated})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())