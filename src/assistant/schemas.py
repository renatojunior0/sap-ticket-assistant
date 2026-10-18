from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Status(str, Enum):
    RESPONDIDO = "RESPONDIDO"
    AGUARDANDO_INFORMACOES = "AGUARDANDO_INFORMACOES"
    FORA_ESCOPO = "FORA_ESCOPO"
    ESCALADO_HUMANO = "ESCALADO_HUMANO"


class TriageResult(BaseModel):
    resumo: str = Field(description="Resumo do problema em uma frase")
    modulo: str = Field(description="Módulo SAP provável (MM, SD, FI...) ou 'DESCONHECIDO'")
    processo: str = Field(description="Chave do processo da ontologia ou 'desconhecido'")
    transacoes: list[str] = Field(default_factory=list, description="Transações citadas ou inferidas")
    mensagens_erro: list[str] = Field(default_factory=list, description="Códigos de mensagem, ex: M7053")
    numeros_documento: list[str] = Field(default_factory=list, description="Pedidos, faturas, IDocs citados")
    fora_escopo: bool = False
    motivo_fora_escopo: Optional[str] = None
    completo: bool = True
    informacoes_faltantes: list[str] = Field(default_factory=list)
    perguntas_ao_usuario: list[str] = Field(default_factory=list)


class Causa(BaseModel):
    descricao: str
    probabilidade: str = Field(description="alta | media | baixa")
    fontes: list[str] = Field(description="IDs de fontes, ex: KB-MM-003")


class Verificacao(BaseModel):
    descricao: str
    transacao: Optional[str] = None
    fontes: list[str] = Field(default_factory=list)


class AcaoHumana(BaseModel):
    descricao: str
    motivo_risco: str
    responsavel_sugerido: str


class AnalysisResult(BaseModel):
    diagnostico: str
    causas: list[Causa]
    verificacoes_somente_leitura: list[Verificacao]
    acoes_requerem_autorizacao: list[AcaoHumana]
    resposta_sugerida_ao_usuario: str
    autoavaliacao_confianca: float = Field(ge=0, le=1)
    lacunas: list[str] = Field(default_factory=list, description="O que a base não cobre")


class SourceRef(BaseModel):
    id: str
    titulo: str
    secao: str
    score: float


class FinalResponse(BaseModel):
    ticket_id: str
    status: Status
    triage: TriageResult
    analysis: Optional[AnalysisResult] = None
    dados_sap_consultados: dict = Field(default_factory=dict)
    fontes: list[SourceRef] = Field(default_factory=list)
    confianca: float = 0.0
    nivel_confianca: str = "BAIXA"
    requer_humano: bool = True
    motivos_humano: list[str] = Field(default_factory=list)
    mensagem_ao_usuario: str = ""
    latencia_ms: int = 0