"""Testes dos schemas de dominio."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assistente.schemas import Recommendation, Signal, StockAnalysis


def test_stock_analysis_matches_descritivo_example():
    analysis = StockAnalysis(
        ticker="VALE3",
        date="2024-11-15",
        close=61.42,
        rsi=45.2,
        macd_signal=Signal.BULLISH,
        news_sentiment=0.72,
        recommendation=Recommendation.COMPRAR,
    )
    assert analysis.recommendation == "COMPRAR"
    assert analysis.macd_signal == "bullish"


def test_sentiment_out_of_range_is_rejected():
    with pytest.raises(ValidationError):
        StockAnalysis(ticker="PETR4", date="2024-11-15", close=30.0, news_sentiment=2.0)


def test_defaults():
    analysis = StockAnalysis(ticker="ITUB4", date="2024-11-15", close=30.0)
    assert analysis.recommendation == Recommendation.AGUARDAR
    assert analysis.macd_signal == Signal.NEUTRAL
