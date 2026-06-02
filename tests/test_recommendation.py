"""Testes da agregacao de sinais em recomendacao (puro, sem rede)."""

from __future__ import annotations

from assistente.schemas import Recommendation
from assistente.tools.recommendation import score_signals

_BULLISH = {
    "rsi": 28,  # sobrevendido -> compra
    "macd_signal": "bullish",
    "trend": "bullish",
    "bollinger_position": 0.05,  # perto da banda inferior
}
_BEARISH = {
    "rsi": 75,  # sobrecomprado -> venda
    "macd_signal": "bearish",
    "trend": "bearish",
    "bollinger_position": 0.95,
}


def test_bullish_signals_lead_to_buy():
    out = score_signals(_BULLISH, sentiment=0.8)
    assert out["recommendation"] == Recommendation.COMPRAR.value
    assert out["weighted_score"] > 0


def test_bearish_signals_lead_to_sell():
    out = score_signals(_BEARISH, sentiment=-0.8)
    assert out["recommendation"] == Recommendation.VENDER.value
    assert out["weighted_score"] < 0


def test_mixed_signals_lead_to_wait():
    neutral = {"rsi": 50, "macd_signal": "neutral", "trend": "neutral", "bollinger_position": 0.5}
    out = score_signals(neutral, sentiment=0.0)
    assert out["recommendation"] == Recommendation.AGUARDAR.value


def test_score_is_bounded():
    out = score_signals(_BULLISH, sentiment=5.0)  # sentimento fora de faixa e saturado
    assert -1.0 <= out["components"]["sentiment"] <= 1.0
