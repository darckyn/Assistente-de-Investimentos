"""Agregacao de sinais em uma recomendacao (COMPRAR / VENDER / AGUARDAR).

Combina, de forma deterministica e explicavel, os indicadores tecnicos com o
score de sentimento. Serve de baseline para o agente orquestrador (que pode
confirmar ou ajustar) e como motor reproduzivel para o backtest.
"""

from __future__ import annotations

from assistente.schemas import Recommendation

# Pesos de cada componente no score final (somam 1.0).
_WEIGHTS = {"rsi": 0.2, "macd": 0.25, "trend": 0.25, "bollinger": 0.1, "sentiment": 0.2}

# Limiares de decisao sobre o score combinado [-1, +1].
_BUY_THRESHOLD = 0.2
_SELL_THRESHOLD = -0.2


def _rsi_component(rsi: float | None) -> float:
    if rsi is None:
        return 0.0
    if rsi <= 30:
        return 1.0  # sobrevendido -> vies de compra
    if rsi >= 70:
        return -1.0  # sobrecomprado -> vies de venda
    # Entre 30 e 70: leve inclinacao contraria ao extremo mais proximo.
    return round((50 - rsi) / 20, 3)


def _signal_component(signal: str | None) -> float:
    return {"bullish": 1.0, "bearish": -1.0}.get(signal or "", 0.0)


def _bollinger_component(position: float | None) -> float:
    if position is None:
        return 0.0
    # position 0 = banda inferior (compra), 1 = banda superior (venda).
    return round((0.5 - position) * 2, 3)


def score_signals(indicators: dict, sentiment: float) -> dict:
    """Calcula o score combinado e a recomendacao sugerida.

    Args:
        indicators: dict de ``compute_indicators`` (rsi, macd_signal, trend, ...).
        sentiment: score agregado de sentimento das noticias (-1 a +1).

    Returns:
        dict com componentes, score total e ``recommendation`` sugerida.
    """
    components = {
        "rsi": _rsi_component(indicators.get("rsi")),
        "macd": _signal_component(indicators.get("macd_signal")),
        "trend": _signal_component(indicators.get("trend")),
        "bollinger": _bollinger_component(indicators.get("bollinger_position")),
        "sentiment": max(-1.0, min(1.0, float(sentiment))),
    }
    total = round(sum(components[k] * _WEIGHTS[k] for k in _WEIGHTS), 4)

    if total >= _BUY_THRESHOLD:
        rec = Recommendation.COMPRAR
    elif total <= _SELL_THRESHOLD:
        rec = Recommendation.VENDER
    else:
        rec = Recommendation.AGUARDAR

    return {
        "components": components,
        "weighted_score": total,
        "recommendation": rec.value,
    }


def generate_recommendation(ticker: str, period: str = "6mo") -> dict:
    """Gera uma recomendacao baseline combinando indicadores tecnicos e sentimento.

    Coleta os dados internamente (indicadores + sentimento das noticias) e devolve
    um score explicavel com a recomendacao sugerida. O agente orquestrador usa este
    resultado como evidencia quantitativa para a decisao final.

    Args:
        ticker: Codigo da acao na B3 (ex.: "VALE3").
        period: Janela historica para os indicadores.

    Returns:
        dict com status, score por componente, score combinado e recomendacao.
    """
    from assistente.tools.indicators import calculate_indicators
    from assistente.tools.sentiment import analyze_news_sentiment

    indicators = calculate_indicators(ticker, period)
    if indicators["status"] != "success":
        return indicators

    sentiment_result = analyze_news_sentiment(ticker)
    sentiment_score = (
        sentiment_result.get("aggregate_sentiment", 0.0)
        if sentiment_result.get("status") == "success"
        else 0.0
    )

    scored = score_signals(indicators, sentiment_score)
    return {
        "status": "success",
        "ticker": ticker.upper(),
        "period": period,
        "last_close": indicators.get("close"),
        "rsi": indicators.get("rsi"),
        "macd_signal": indicators.get("macd_signal"),
        "trend": indicators.get("trend"),
        "news_sentiment": sentiment_score,
        "sentiment_available": sentiment_result.get("sentiment_available", False),
        **scored,
    }
