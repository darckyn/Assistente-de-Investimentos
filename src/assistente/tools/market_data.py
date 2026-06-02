"""Coleta de precos e volumes (OHLCV) via yfinance.

Expoe ``get_price_data`` como tool do agente e ``fetch_ohlcv`` como helper
interno (retorna DataFrame) reutilizado por indicadores, grafico e backtest.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
import yfinance as yf


def to_yahoo_symbol(ticker: str) -> str:
    """Converte um codigo da B3 para o simbolo do Yahoo Finance.

    Ex.: ``VALE3`` -> ``VALE3.SA``. Codigos que ja tenham sufixo sao preservados.
    """
    t = ticker.strip().upper()
    return t if "." in t else f"{t}.SA"


@lru_cache(maxsize=64)
def _fetch_cached(symbol: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    # yfinance pode devolver colunas MultiIndex quando ha 1 ticker; achata.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Retorna o DataFrame OHLCV (Open/High/Low/Close/Volume) de uma acao.

    Helper interno (nao e tool). Resultado e cacheado por (symbol, period, interval).
    """
    df = _fetch_cached(to_yahoo_symbol(ticker), period, interval)
    return df.copy()


def get_price_data(ticker: str, period: str = "6mo") -> dict:
    """Coleta dados historicos de preco/volume de uma acao da B3.

    Args:
        ticker: Codigo da acao na B3 (ex.: "VALE3", "PETR4").
        period: Janela historica (ex.: "1mo", "3mo", "6mo", "1y", "2y").

    Returns:
        dict com status e um resumo: ultimo fechamento, variacao no periodo,
        maxima/minima, volume medio e os ultimos 5 pregoes.
    """
    try:
        df = fetch_ohlcv(ticker, period)
        if df.empty:
            return {"status": "error", "error_message": f"Sem dados para {ticker}."}

        close = df["Close"].dropna()
        first, last = float(close.iloc[0]), float(close.iloc[-1])
        change_pct = (last / first - 1.0) * 100.0 if first else 0.0

        recent = (
            df.tail(5)
            .reset_index()
            .assign(Date=lambda d: d.iloc[:, 0].astype(str).str.slice(0, 10))
        )
        recent_rows = [
            {
                "date": row["Date"],
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
            }
            for _, row in recent.iterrows()
        ]

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "period": period,
            "last_close": round(last, 2),
            "period_change_pct": round(change_pct, 2),
            "period_high": round(float(df["High"].max()), 2),
            "period_low": round(float(df["Low"].min()), 2),
            "avg_volume": int(df["Volume"].mean()),
            "recent": recent_rows,
        }
    except Exception as exc:
        return {"status": "error", "error_message": f"Falha ao coletar {ticker}: {exc}"}
