import re
from functools import lru_cache

import yaml

from . import config


@lru_cache(maxsize=1)
def load_ontology() -> dict:
    with open(config.ONTOLOGY_PATH, encoding="utf-8") as file:
        return yaml.safe_load(file)


def summary_for_prompt() -> str:
    ontology = load_ontology()
    lines = [f"Módulo: {ontology['modulo']}", f"Fora de escopo: {ontology['fora_escopo']}", "Processos:"]
    for key, process in ontology["processos"].items():
        lines.append(
            f"- {key}: {process['nome']} | transações: {', '.join(process.get('transacoes', []))}"
            f" | mensagens: {', '.join(process.get('mensagens', []))}"
            f" | informações mínimas: {', '.join(process.get('informacoes_minimas', []))}"
        )
    return "\n".join(lines)


def infer_process(text: str) -> str | None:
    """Fallback determinístico: mapeia transação/mensagem citada → processo."""
    tokens = set(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", text.upper()))
    for key, process in load_ontology()["processos"].items():
        vocabulary = set(process.get("transacoes", [])) | set(process.get("mensagens", []))
        if tokens & vocabulary:
            return key
    return None


def process_vocabulary(process_key: str) -> set[str]:
    process = load_ontology()["processos"].get(process_key, {})
    return {
        term.upper()
        for field in ("transacoes", "mensagens", "tabelas", "objetos_autorizacao")
        for term in process.get(field, [])
    }


def critical_actions() -> list[str]:
    return [action.lower() for action in load_ontology()["acoes_criticas"]]

@lru_cache(maxsize=1)
def load_catalog() -> dict:
    path = config.ONTOLOGY_PATH.parent / "transacoes_catalogo.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def modules_mentioned(text: str) -> set[str]:
    """Módulos das transações citadas no chamado, segundo o catálogo corporativo (ex.: PA30 -> HR)."""
    tokens = set(re.findall(r"\b/?[A-Z][A-Z0-9_]{2,}\b", text.upper()))
    return {load_catalog()[t]["modulo"] for t in tokens if t in load_catalog()}
