import json
import logging
import re
from typing import Any, TypeVar

from openai import APIConnectionError, BadRequestError, InternalServerError, NotFoundError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import Settings, load_fallback_settings, load_settings

T = TypeVar("T", bound=BaseModel)
MAX_SCHEMA_ATTEMPTS = 2
RETRYABLE_ERRORS = (RateLimitError, APIConnectionError, InternalServerError)
FALLBACK_ERRORS = RETRYABLE_ERRORS + (NotFoundError,)
STRICT_SCHEMA_PROVIDERS = {"ollama"}  # provedores onde o schema é imposto por gramática no servidor
ENVELOPE_KEYS = ("properties", "data", "result", "output", "response")
log = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("Nenhum objeto JSON na resposta", text[:200], 0)
    return match.group(0)


def _unwrap(payload: Any, schema: type[BaseModel]) -> Any:
    """Modelos pequenos devolvem o schema preenchido ({'properties': {...}}) ou um envelope ({'TriageResult': {...}})."""
    if not isinstance(payload, dict):
        return payload
    fields = set(schema.model_fields)
    if fields & payload.keys():
        return payload
    for key in (schema.__name__, *ENVELOPE_KEYS):
        inner = payload.get(key)
        if isinstance(inner, dict) and fields & inner.keys():
            return inner
    if len(payload) == 1:
        return _unwrap(next(iter(payload.values())), schema)
    return payload


def _parse(raw: str, schema: type[T]) -> T:
    payload = _unwrap(json.loads(_extract_json(raw)), schema)
    return schema.model_validate(payload)


def _correction_message(error: Exception, schema: type[BaseModel]) -> str:
    return (
        f"Resposta rejeitada: {str(error)[:400]}\n"
        f"Devolva APENAS um objeto JSON com os valores preenchidos, sem 'properties', 'type' ou 'description'. "
        f"Chaves obrigatórias no nível raiz: {list(schema.model_fields)}."
    )


class LLMClient:
    def __init__(self, settings: Settings | None = None, fallback: Settings | None = None):
        self.settings = settings or load_settings()
        self.fallback = fallback if fallback is not None else load_fallback_settings()
        self._clients = {
            s.provider: OpenAI(base_url=s.base_url, api_key=s.api_key)
            for s in (self.settings, self.fallback) if s is not None
        }
        self.last_used: Settings = self.settings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6),
           retry=retry_if_exception_type(RETRYABLE_ERRORS), reraise=True)
    def _call(self, settings: Settings, messages: list[dict], temperature: float, response_format: dict | None) -> str:
        kwargs = {"response_format": response_format} if response_format else {}
        response = self._clients[settings.provider].chat.completions.create(
            model=settings.model, messages=messages, temperature=temperature, **kwargs
        )
        return response.choices[0].message.content or ""

    def _call_json(self, settings: Settings, messages: list[dict], temperature: float, schema: type[BaseModel]) -> str:
        if settings.provider in STRICT_SCHEMA_PROVIDERS:
            strict = {"type": "json_schema", "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()}}
            try:
                return self._call(settings, messages, temperature, strict)
            except BadRequestError:  # versão do servidor sem suporte a json_schema
                log.warning("%s não aceitou json_schema; usando json_object", settings.provider)
        return self._call(settings, messages, temperature, {"type": "json_object"})

    def _with_fallback(self, fn, *args):
        self.last_used = self.settings
        try:
            return fn(self.settings, *args)
        except FALLBACK_ERRORS as error:
            if self.fallback is None:
                raise
            log.warning("Provedor '%s' falhou (%s); usando fallback '%s'",
                        self.settings.provider, type(error).__name__, self.fallback.provider)
            self.last_used = self.fallback
            return fn(self.fallback, *args)

    def _complete_json_on(self, settings: Settings, system_prompt: str, user_prompt: str,
                          schema: type[T], temperature: float) -> T:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        last_error: Exception | None = None
        for _ in range(MAX_SCHEMA_ATTEMPTS):
            raw = self._call_json(settings, messages, temperature, schema)
            try:
                return _parse(raw, schema)
            except (ValidationError, json.JSONDecodeError) as error:
                last_error = error
                messages += [{"role": "assistant", "content": raw},
                             {"role": "user", "content": _correction_message(error, schema)}]
        raise RuntimeError(f"[{settings.provider}/{settings.model}] JSON inválido após {MAX_SCHEMA_ATTEMPTS} tentativas: {last_error}")

    def complete_json(self, system_prompt: str, user_prompt: str, schema: type[T], temperature: float = 0.0) -> T:
        try:
            return self._with_fallback(self._complete_json_on, system_prompt, user_prompt, schema, temperature)
        except RuntimeError as error:
            if self.fallback is None or self.last_used is self.fallback:
                raise
            log.warning("%s; tentando fallback '%s'", error, self.fallback.provider)
            self.last_used = self.fallback
            return self._complete_json_on(self.fallback, system_prompt, user_prompt, schema, temperature)

    def complete_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        return self._with_fallback(self._call, messages, temperature, None)


_default_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


def chat_json(system_prompt: str, user_prompt: str, schema: type[T], temperature: float = 0.1) -> T:
    return get_client().complete_json(system_prompt, user_prompt, schema, temperature)
