"""Testes do calculo de indicadores (sem rede)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from assistente.tools.indicators import compute_indicators


def _synthetic_ohlcv(n: int = 80, trend: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    base = 50 + np.arange(n) * trend
    close = base + np.sin(np.arange(n) / 3.0)
    return pd.DataFrame(
        {
            "Open": close - 0.3,
            "High": close + 0.6,
            "Low": close - 0.6,
            "Close": close,
            "Volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


def test_compute_indicators_keys_and_ranges():
    result = compute_indicators(_synthetic_ohlcv())
    expected = {"close", "rsi", "macd_signal", "trend", "bollinger_position", "volume_ratio"}
    assert expected <= result.keys()
    assert 0 <= result["rsi"] <= 100
    assert result["macd_signal"] in {"bullish", "bearish", "neutral"}


def test_uptrend_is_bullish():
    result = compute_indicators(_synthetic_ohlcv(trend=0.8))
    assert result["trend"] == "bullish"


def test_downtrend_is_bearish():
    result = compute_indicators(_synthetic_ohlcv(trend=-0.8))
    assert result["trend"] == "bearish"
