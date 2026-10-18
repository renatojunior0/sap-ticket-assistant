"""Valida conectividade e saída JSON do provedor configurado. Uso: python scripts/check_llm.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pydantic import BaseModel
from assistant.config import load_settings
from assistant.llm import LLMClient


class Ping(BaseModel):
    modulo: str
    transacao: str


def main() -> None:
    settings = load_settings()
    print(f"provider={settings.provider} model={settings.model}")

    client = LLMClient(settings)
    result = client.complete_json(
        system_prompt="Você é um assistente SAP. Responda SOMENTE em JSON com as chaves 'modulo' e 'transacao'.",
        user_prompt="Qual módulo e transação são usados para criar um pedido de compra?",
        schema=Ping,
    )
    print(f"OK -> {result.model_dump()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FALHA [{type(exc).__name__}]: {str(exc)[:300]}")
        sys.exit(1)