"""Calculo de indicadores tecnicos com pandas-ta-classic.

Cobre RSI, MACD, SMA/EMA, Bandas de Bollinger e volume. ``compute_indicators``
e o helper puro (recebe DataFrame, devolve dict); ``calculate_indicators`` e a
tool do agente (recebe ticker/period).
"""

from __future__ import annotations

import math

import pandas as pd
import pandas_ta_classic as ta

from assistente.tools.market_data import fetch_ohlcv


def _last(series: pd.Series | None) -> float | None:
    """Ultimo valor valido de uma Series, ou None."""
    if series is None or series.dropna().empty:
        return None
    value = float(series.dropna().iloc[-1])
    return None if math.isnan(value) else round(value, 4)


def _macd_columns(macd_df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Extrai (linha MACD, histograma, linha de sinal) de forma robusta a nomes."""
    line = macd_df.filter(like="MACD_").iloc[:, 0]
    hist = macd_df.filter(like="MACDh_").iloc[:, 0]
    signal = macd_df.filter(like="MACDs_").iloc[:, 0]
    return line, hist, signal


def compute_indicators(df: pd.DataFrame) -> dict:
    """Calcula os indicadores tecnicos a partir de um DataFrame OHLCV."""
    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    rsi = _last(ta.rsi(close, length=14))

    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    macd_line = macd_hist = macd_sig = None
    macd_signal = "neutral"
    if macd_df is not None and not macd_df.dropna().empty:
        line, hist, sig = _macd_columns(macd_df)
        macd_line, macd_hist, macd_sig = _last(line), _last(hist), _last(sig)
        if macd_line is not None and macd_sig is not None:
            macd_signal = "bullish" if macd_line >= macd_sig else "bearish"

    sma20, sma50 = _last(ta.sma(close, length=20)), _last(ta.sma(close, length=50))
    ema9, ema21 = _last(ta.ema(close, length=9)), _last(ta.ema(close, length=21))

    trend = "neutral"
    if sma20 is not None and sma50 is not None:
        trend = "bullish" if sma20 >= sma50 else "bearish"

    bbands = ta.bbands(close, length=20, std=2)
    bb_lower = bb_mid = bb_upper = bb_position = None
    if bbands is not None and not bbands.dropna().empty:
        bb_lower = _last(bbands.filter(like="BBL_").iloc[:, 0])
        bb_mid = _last(bbands.filter(like="BBM_").iloc[:, 0])
        bb_upper = _last(bbands.filter(like="BBU_").iloc[:, 0])
        last_close = _last(close)
        if None not in (bb_lower, bb_upper, last_close) and bb_upper > bb_lower:
            bb_position = round((last_close - bb_lower) / (bb_upper - bb_lower), 3)

    last_vol = _last(volume)
    avg_vol = _last(volume.rolling(20).mean())
    vol_ratio = round(last_vol / avg_vol, 2) if last_vol and avg_vol else None

    rsi_zone = "neutral"
    if rsi is not None:
        rsi_zone = "overbought" if rsi >= 70 else "oversold" if rsi <= 30 else "neutral"

    return {
        "close": _last(close),
        "rsi": rsi,
        "rsi_zone": rsi_zone,
        "macd": macd_line,
        "macd_histogram": macd_hist,
        "macd_signal_line": macd_sig,
        "macd_signal": macd_signal,
        "sma_20": sma20,
        "sma_50": sma50,
        "ema_9": ema9,
        "ema_21": ema21,
        "trend": trend,
        "bollinger_lower": bb_lower,
        "bollinger_middle": bb_mid,
        "bollinger_upper": bb_upper,
        "bollinger_position": bb_position,
        "volume_ratio": vol_ratio,
    }


def calculate_indicators(ticker: str, period: str = "6mo") -> dict:
    """Calcula indicadores tecnicos (RSI, MACD, SMA/EMA, Bollinger, volume) de uma acao.

    Args:
        ticker: Codigo da acao na B3 (ex.: "VALE3").
        period: Janela historica usada no calculo (ex.: "6mo", "1y").

    Returns:
        dict com status e os valores dos indicadores, incluindo zonas/sinais
        derivados (rsi_zone, macd_signal, trend, bollinger_position).
    """
    try:
        df = fetch_ohlcv(ticker, period)
        if df.empty or len(df) < 30:
            return {
                "status": "error",
                "error_message": f"Historico insuficiente para {ticker} (period={period}).",
            }
        result = compute_indicators(df)
        result.update({"status": "success", "ticker": ticker.upper(), "period": period})
        return result
    except Exception as exc:
        return {"status": "error", "error_message": f"Falha nos indicadores de {ticker}: {exc}"}
