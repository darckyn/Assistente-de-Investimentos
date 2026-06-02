"""Geracao de grafico de candles com indicadores (mplfinance).

Exposta como tool do agente: produz um PNG (candles + medias moveis + Bandas de
Bollinger + volume) e retorna o caminho do arquivo para exibicao na interface.
"""

from __future__ import annotations

from pathlib import Path

import mplfinance as mpf
import pandas_ta_classic as ta

from assistente.tools.market_data import fetch_ohlcv, to_yahoo_symbol

CHARTS_DIR = Path("charts")


def plot_chart(ticker: str, period: str = "6mo") -> dict:
    """Gera um grafico de candles com SMA(20/50), Bandas de Bollinger e volume.

    Args:
        ticker: Codigo da acao na B3 (ex.: "PETR4").
        period: Janela historica exibida (ex.: "3mo", "6mo", "1y").

    Returns:
        dict com status e ``image_path`` (PNG salvo em disco).
    """
    try:
        df = fetch_ohlcv(ticker, period)
        if df.empty:
            return {"status": "error", "error_message": f"Sem dados para {ticker}."}

        ohlc = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        bbands = ta.bbands(ohlc["Close"], length=20, std=2)

        addplots = []
        if bbands is not None and not bbands.dropna().empty:
            addplots = [
                mpf.make_addplot(bbands.filter(like="BBU_").iloc[:, 0], color="gray", width=0.7),
                mpf.make_addplot(bbands.filter(like="BBL_").iloc[:, 0], color="gray", width=0.7),
            ]

        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        image_path = CHARTS_DIR / f"{to_yahoo_symbol(ticker)}_{period}.png"

        mpf.plot(
            ohlc,
            type="candle",
            style="yahoo",
            mav=(20, 50),
            volume=True,
            addplot=addplots,
            title=f"{ticker.upper()} - {period}",
            savefig=dict(fname=str(image_path), dpi=120, bbox_inches="tight"),
        )

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "period": period,
            "image_path": str(image_path),
        }
    except Exception as exc:
        return {"status": "error", "error_message": f"Falha ao gerar grafico de {ticker}: {exc}"}
