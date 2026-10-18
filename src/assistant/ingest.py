import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config

CHUNKS_PATH = config.ROOT / "data" / "kb_chunks.jsonl"
MANIFEST_PATH = config.ROOT / "data" / "kb_manifest.yaml"


@dataclass
class Chunk:
    id: str
    doc_id: str
    titulo: str
    secao: str
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def processos(self) -> set[str]:
        return set(self.metadata.get("processos", []))

    @property
    def searchable_text(self) -> str:
        tags = " ".join(str(v) for k in ("transacoes", "mensagens", "tabelas") for v in self.metadata.get(k, []))
        return f"{self.titulo}\n{self.secao}\n{self.text}\n{tags}"


def _parse_front_matter(raw: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, flags=re.DOTALL)
    return (yaml.safe_load(match.group(1)) or {}, match.group(2)) if match else ({}, raw)


def load_article_chunks() -> list[Chunk]:
    """Um chunk por seção '## ' de cada artigo curado; metadados do front-matter."""
    chunks = []
    for path in sorted(config.KB_DIR.glob("*.md")):
        metadata, body = _parse_front_matter(path.read_text(encoding="utf-8"))
        metadata.setdefault("processos", [metadata["processo"]] if metadata.get("processo") else [])
        metadata["tipo"] = "artigo_curado"
        doc_id, titulo = metadata.get("id", path.stem), metadata.get("titulo", path.stem)
        for index, section in enumerate(s for s in re.split(r"^## ", body, flags=re.MULTILINE) if s.strip()):
            heading, _, content = section.partition("\n")
            chunks.append(Chunk(f"{doc_id}#{index}", doc_id, titulo, heading.strip(), content.strip(), metadata))
    return chunks


def load_document_chunks() -> list[Chunk]:
    """Chunks dos documentos de referência (PDF/DOCX) gerados por scripts/ingest_kb.py."""
    if not CHUNKS_PATH.exists():
        return []
    processes_by_source = {}
    if MANIFEST_PATH.exists():
        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        processes_by_source = {d["arquivo"]: d.get("processos", []) for d in manifest.get("documentos", [])}
    chunks = []
    for line in CHUNKS_PATH.open(encoding="utf-8"):
        record = json.loads(line)
        source = record["source"]
        metadata = {"tipo": "documento", "processos": processes_by_source.get(source, []), "modo": record.get("mode")}
        chunks.append(Chunk(record["id"], Path(source).stem, source, f"p. {record.get('pages', '?')}", record["text"], metadata))
    return chunks


def load_chunks() -> list[Chunk]:
    chunks = load_article_chunks() + load_document_chunks()
    if not chunks:
        raise RuntimeError("Base vazia: nenhum artigo em data/knowledge_base nem data/kb_chunks.jsonl")
    return chunks