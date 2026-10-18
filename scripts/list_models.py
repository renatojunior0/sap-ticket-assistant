"""Lista modelos de chat disponíveis no provedor configurado. Uso: LLM_PROVIDER=groq python scripts/list_models.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assistant.config import list_chat_models, load_settings


def main() -> None:
    settings = load_settings(resolve_model=False)
    print(f"provider={settings.provider}")
    for model_id in list_chat_models(settings):
        print(f"  {model_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FALHA [{type(exc).__name__}]: {str(exc)[:300]}")
        sys.exit(1)