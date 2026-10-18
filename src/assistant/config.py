import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]  # .../sap-ticket-assistant
load_dotenv(ROOT / ".env")  # variáveis já exportadas no shell têm prioridade

DATA_DIR = ROOT / "data"
KB_DIR = DATA_DIR / "knowledge_base"
CHUNKS_PATH = DATA_DIR / "kb_chunks.jsonl"
MANIFEST_PATH = DATA_DIR / "kb_manifest.yaml"
ONTOLOGY_PATH = DATA_DIR / "ontology" / "mm_ontology.yaml"
CATALOG_PATH = DATA_DIR / "ontology" / "transacoes_catalogo.yaml"
TICKETS_PATH = DATA_DIR / "tickets" / "tickets.json"
AUDIT_PATH = ROOT / "logs" / "audit.jsonl"
CACHE_DIR = ROOT / ".cache"

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "openai/gpt-oss-120b",
        "preferences": ["openai/gpt-oss-120b", "qwen", "openai/gpt-oss-20b", "llama"],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
        "preferences": ["gemini-2.5-flash", "gemini-2.0-flash"],
    },
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "key_env": None,
        "model_env": "OLLAMA_MODEL",
        "default_model": "llama3.1:8b",
        "preferences": ["llama3.1", "qwen"],
    },
}
NON_CHAT_MARKERS = ("whisper", "tts", "embedding", "guard", "vision", "image", "audio", "imagen", "veo", "aqa")
_DEFAULT_FALLBACK = {"groq": "gemini", "gemini": "groq", "ollama": "groq"}

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
if LLM_PROVIDER not in PROVIDERS:
    raise ValueError(f"LLM_PROVIDER inválido: '{LLM_PROVIDER}'. Use: {', '.join(PROVIDERS)}")

LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", _DEFAULT_FALLBACK[LLM_PROVIDER]).lower() or None
if LLM_FALLBACK_PROVIDER and LLM_FALLBACK_PROVIDER not in PROVIDERS:
    raise ValueError(f"LLM_FALLBACK_PROVIDER inválido: '{LLM_FALLBACK_PROVIDER}'. Use: {', '.join(PROVIDERS)}")


def _resolve_model(provider: str) -> str:
    preset = PROVIDERS[provider]
    return os.getenv(preset["model_env"]) or os.getenv("LLM_MODEL") or preset["default_model"]


LLM_MODEL = _resolve_model(LLM_PROVIDER)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

TOP_K = int(os.getenv("TOP_K", "5"))
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.35"))
CONFIDENCE_HIGH = 0.75
CONFIDENCE_LOW = 0.50


@dataclass(frozen=True)
class Settings:
    provider: str
    base_url: str
    api_key: str
    model: str


def load_settings(provider: str | None = None) -> Settings:
    name = (provider or LLM_PROVIDER).lower()
    preset = PROVIDERS[name]
    api_key = os.getenv(preset["key_env"], "") if preset["key_env"] else "ollama"
    if not api_key:
        raise EnvironmentError(f"Defina {preset['key_env']} no .env para usar o provedor '{name}'.")
    return Settings(provider=name, base_url=preset["base_url"], api_key=api_key, model=_resolve_model(name))


def load_fallback_settings() -> Settings | None:
    """Fallback só existe se for um provedor diferente do principal e tiver chave configurada."""
    if not LLM_FALLBACK_PROVIDER or LLM_FALLBACK_PROVIDER == LLM_PROVIDER:
        return None
    try:
        return load_settings(LLM_FALLBACK_PROVIDER)
    except EnvironmentError:
        return None


def list_chat_models(settings: Settings) -> list[str]:
    client = OpenAI(base_url=settings.base_url, api_key=settings.api_key)
    ids = (m.id.removeprefix("models/") for m in client.models.list().data)  # Gemini prefixa "models/"; Groq usa "org/x"
    return sorted(i for i in ids if not any(marker in i.lower() for marker in NON_CHAT_MARKERS))