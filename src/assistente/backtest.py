"""Backtest das recomendacoes vs comportamento real e vs Buy-and-Hold.

Para manter o custo previsivel e o resultado reproduzivel, o backtest usa o motor
DETERMINISTICO (`compute_indicators` + `score_signals`) -- o mesmo baseline que o
orquestrador consulta -- em vez de chamar o LLM para cada dia historico.

Os indicadores sao rolling/causais (so usam dados ate o dia t), portanto nao ha
lookahead. O sentimento de noticias nao tem historico facilmente disponivel, logo
o backtest e tecnico (sentimento = 0); isso e uma limitacao explicita.
"""

from __future__ import annotations

import pandas as pd
import pandas_ta_classic as ta

from assistente.schemas import Recommendation
from assistente.tools.market_data import fetch_ohlcv
from assistente.tools.recommendation import score_signals


def build_signal_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula, de forma vetorizada e causal, os sinais diarios e a recomendacao."""
    close = df["Close"].astype(float)
    out = pd.DataFrame(index=df.index)
    out["close"] = close
    out["rsi"] = ta.rsi(close, length=14)

    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    macd_line = macd_df.filter(like="MACD_").iloc[:, 0]
    macd_sig = macd_df.filter(like="MACDs_").iloc[:, 0]
    out["macd_signal"] = (macd_line >= macd_sig).map({True: "bullish", False: "bearish"})

    sma20, sma50 = ta.sma(close, length=20), ta.sma(close, length=50)
    out["trend"] = (sma20 >= sma50).map({True: "bullish", False: "bearish"})

    bbands = ta.bbands(close, length=20, std=2)
    bb_l = bbands.filter(like="BBL_").iloc[:, 0]
    bb_u = bbands.filter(like="BBU_").iloc[:, 0]
    out["bollinger_position"] = (close - bb_l) / (bb_u - bb_l)

    out["recommendation"] = [
        score_signals(row, sentiment=0.0)["recommendation"]
        for row in out[["rsi", "macd_signal", "trend", "bollinger_position"]].to_dict("records")
    ]
    return out.dropna()


def run_backtest(
    ticker: str,
    period: str = "2y",
    horizon: int = 5,
    wait_threshold: float = 0.01,
) -> dict:
    """Roda o backtest de uma acao.

    Args:
        ticker: Codigo da acao na B3 (ex.: "VALE3").
        period: Janela historica total do teste.
        horizon: Dias a frente para medir o acerto de tendencia.
        wait_threshold: Faixa (|retorno|) considerada "de lado" para AGUARDAR.

    Returns:
        dict com acuracia (acerto de tendencia), distribuicao de sinais, retorno da
        estrategia e do Buy-and-Hold, e a diferenca (outperformance).
    """
    df = fetch_ohlcv(ticker, period)
    if df.empty or len(df) < 60:
        return {"status": "error", "error_message": f"Historico insuficiente para {ticker}."}

    signals = build_signal_frame(df)
    close = signals["close"]

    # Retorno futuro em `horizon` dias para avaliar o acerto de tendencia.
    fwd_return = close.shift(-horizon) / close - 1.0
    evaluable = signals.assign(fwd_return=fwd_return).dropna(subset=["fwd_return"])

    def _is_hit(rec: str, ret: float) -> bool:
        if rec == Recommendation.COMPRAR.value:
            return ret > wait_threshold
        if rec == Recommendation.VENDER.value:
            return ret < -wait_threshold
        return abs(ret) <= wait_threshold  # AGUARDAR

    hits = [_is_hit(r.recommendation, r.fwd_return) for r in evaluable.itertuples()]
    accuracy = round(sum(hits) / len(hits), 4) if hits else 0.0

    # Simulacao long-only: investido no dia seguinte a um sinal COMPRAR.
    daily_return = close.pct_change().fillna(0.0)
    position = (signals["recommendation"] == Recommendation.COMPRAR.value).shift(1).fillna(False)
    strategy_daily = daily_return * position.astype(float)
    strategy_return = round(float((1 + strategy_daily).prod() - 1) * 100, 2)
    buy_hold_return = round(float(close.iloc[-1] / close.iloc[0] - 1) * 100, 2)

    distribution = signals["recommendation"].value_counts().to_dict()

    return {
        "status": "success",
        "ticker": ticker.upper(),
        "period": period,
        "horizon_days": horizon,
        "n_signals": len(evaluable),
        "accuracy": accuracy,
        "signal_distribution": {str(k): int(v) for k, v in distribution.items()},
        "strategy_return_pct": strategy_return,
        "buy_hold_return_pct": buy_hold_return,
        "outperformance_pct": round(strategy_return - buy_hold_return, 2),
    }


def run_backtest_all(tickers: list[str], **kwargs) -> pd.DataFrame:
    """Roda o backtest para varios tickers e consolida em um DataFrame."""
    rows = [run_backtest(t, **kwargs) for t in tickers]
    return pd.DataFrame([r for r in rows if r.get("status") == "success"])
