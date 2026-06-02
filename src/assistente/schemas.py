"""Schemas de dados do dominio.

``StockAnalysis`` consolida o resultado de analise de uma acao em um dia, no
formato esperado pelo descritivo do projeto, acrescido do raciocinio
(Chain-of-Thought) que e criterio de avaliacao.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Recommendation(StrEnum):
    """Acao recomendada pelo agente."""

    COMPRAR = "COMPRAR"
    VENDER = "VENDER"
    AGUARDAR = "AGUARDAR"


class Signal(StrEnum):
    """Direcao de um sinal tecnico ou de sentimento."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SentimentLabel(StrEnum):
    """Classes de sentimento (FinBERT-PT-BR)."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class StockAnalysis(BaseModel):
    """Resultado consolidado da analise de uma acao em uma data.

    Espelha o exemplo do descritivo:
    ``{"ticker": "VALE3", "date": "2024-11-15", "close": 61.42, "rsi": 45.2,
       "macd_signal": "bullish", "news_sentiment": 0.72, "recommendation": "COMPRAR"}``
    """

    ticker: str
    date: str = Field(description="Data da analise (YYYY-MM-DD).")
    close: float = Field(description="Preco de fechamento mais recente.")
    rsi: float | None = Field(default=None, description="Indice de Forca Relativa (0-100).")
    macd_signal: Signal = Field(default=Signal.NEUTRAL)
    news_sentiment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Score agregado de sentimento das noticias (-1 a +1).",
    )
    recommendation: Recommendation = Field(default=Recommendation.AGUARDAR)
    reasoning: str = Field(
        default="",
        description="Chain-of-Thought: passo a passo que levou a recomendacao.",
    )
