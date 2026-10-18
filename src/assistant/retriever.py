import hashlib
import pickle
import re

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from . import config
from .ingest import Chunk, load_chunks

TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
PROCESS_BOOST, TERM_BOOST, ARTICLE_BOOST = 0.10, 0.15, 0.05


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


class HybridRetriever:
    """BM25 (códigos exatos: ME21N, M7053) + embeddings (semântica PT-BR) fundidos por RRF,
    com reforço por metadados da ontologia (processo e transações detectados na triagem)."""

    def __init__(self):
        self.chunks: list[Chunk] = load_chunks()
        self.bm25 = BM25Okapi([_tokenize(c.searchable_text) for c in self.chunks])
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.embeddings = self._load_or_build_embeddings()

    def _load_or_build_embeddings(self) -> np.ndarray:
        config.CACHE_DIR.mkdir(exist_ok=True)
        fingerprint = hashlib.md5("".join(c.searchable_text for c in self.chunks).encode()).hexdigest()
        cache_file = config.CACHE_DIR / f"emb_{fingerprint}.pkl"
        if cache_file.exists():
            return pickle.loads(cache_file.read_bytes())
        embeddings = self.model.encode([c.searchable_text for c in self.chunks], normalize_embeddings=True,
                                       batch_size=32, show_progress_bar=True)
        cache_file.write_bytes(pickle.dumps(embeddings))
        return embeddings

    def search(self, query: str, boost_terms: set[str] | None = None, process: str | None = None,
               top_k: int = config.TOP_K) -> list[dict]:
        cosine = self.embeddings @ self.model.encode([query], normalize_embeddings=True)[0]
        bm25_scores = np.array(self.bm25.get_scores(_tokenize(query)))

        rrf = np.zeros(len(self.chunks))
        for rank, index in enumerate(np.argsort(-cosine)):
            rrf[index] += 1 / (60 + rank)
        for rank, index in enumerate(np.argsort(-bm25_scores)):
            if bm25_scores[index] > 0:
                rrf[index] += 1 / (60 + rank)

        boost_terms = {t.upper() for t in (boost_terms or set())}
        candidates = []
        for index in np.argsort(-rrf)[: top_k * 4]:
            chunk = self.chunks[index]
            chunk_terms = {str(v).upper() for k in ("transacoes", "mensagens") for v in chunk.metadata.get(k, [])}
            chunk_terms |= set(re.findall(r"\b[A-Z]{2,4}\d{1,2}[A-Z]?\b", chunk.text[:600]))
            score = max(0.0, float(cosine[index]))
            score += TERM_BOOST if boost_terms & chunk_terms else 0
            score += PROCESS_BOOST if process and process in chunk.processos else 0
            score += ARTICLE_BOOST if chunk.metadata.get("tipo") == "artigo_curado" else 0
            candidates.append({"chunk": chunk, "score": round(min(score, 1.0), 4),
                               "cosine": float(cosine[index]), "bm25": float(bm25_scores[index])})
        return sorted(candidates, key=lambda r: -r["score"])[:top_k]


def format_context(results: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{r['chunk'].doc_id}] {r['chunk'].titulo} — {r['chunk'].secao}\n{r['chunk'].text}" for r in results
    )