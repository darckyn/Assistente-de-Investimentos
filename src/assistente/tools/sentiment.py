"""Analise de sentimento de noticias financeiras em portugues (FinBERT-PT-BR).

O modelo (torch + transformers) fica no grupo opcional ``sentiment`` do Poetry e
e carregado de forma preguicosa. Se nao estiver disponivel, a tool ainda retorna
as manchetes e sinaliza ``sentiment_available=False`` para o agente decidir via LLM.
"""

from __future__ import annotations

from functools import lru_cache

from assistente.config import get_settings
from assistente.tools.news import search_news

_LABEL_SCORE = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}


def _label_to_key(label: str) -> str:
    low = label.lower()
    if "pos" in low:
        return "positive"
    if "neg" in low:
        return "negative"
    return "neutral"


@lru_cache(maxsize=1)
def _get_pipeline():
    """Carrega (uma unica vez) o pipeline de classificacao do FinBERT-PT-BR."""
    from transformers import pipeline  # import tardio: depende do grupo `sentiment`

    settings = get_settings()
    return pipeline(
        task="text-classification",
        model=settings.sentiment_model,
        top_k=None,  # devolve a distribuicao completa de probabilidades
        device=-1,  # CPU (inferencia nao precisa de GPU)
    )


def classify_texts(texts: list[str]) -> list[dict]:
    """Classifica uma lista de textos. Cada item: {label, score, key}.

    ``score`` e a probabilidade da classe vencedora; ``key`` em {positive,negative,neutral}.
    Levanta excecao se o modelo nao puder ser carregado (tratado pelo chamador).
    """
    clf = _get_pipeline()
    raw_results = clf(texts, truncation=True, max_length=512)
    out: list[dict] = []
    for scores in raw_results:
        best = max(scores, key=lambda s: s["score"])
        out.append(
            {
                "label": best["label"],
                "score": round(float(best["score"]), 4),
                "key": _label_to_key(best["label"]),
            }
        )
    return out


def _aggregate_score(keys: list[str]) -> float:
    if not keys:
        return 0.0
    return round(sum(_LABEL_SCORE[k] for k in keys) / len(keys), 3)


def analyze_news_sentiment(ticker: str) -> dict:
    """Coleta noticias de uma acao e classifica o sentimento (Positivo/Negativo/Neutro).

    Args:
        ticker: Codigo da acao na B3 (ex.: "ITUB4").

    Returns:
        dict com status, score agregado de sentimento (-1 a +1), contagem por classe
        e as manchetes (com o sentimento individual quando o modelo esta disponivel).
    """
    news_result = search_news(ticker)
    if news_result["status"] != "success":
        return news_result

    headlines = news_result["news"]
    if not headlines:
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "sentiment_available": False,
            "news_count": 0,
            "aggregate_sentiment": 0.0,
            "message": "Nenhuma noticia recente encontrada para o periodo.",
            "headlines": [],
        }

    texts = [f"{h['title']}. {h['summary']}".strip() for h in headlines]

    try:
        classified = classify_texts(texts)
    except Exception as exc:
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "sentiment_available": False,
            "news_count": len(headlines),
            "aggregate_sentiment": 0.0,
            "message": (
                "FinBERT-PT-BR indisponivel "
                f"({type(exc).__name__}); avalie o sentimento pelas manchetes. "
                "Instale com: poetry install --with sentiment"
            ),
            "headlines": headlines,
        }

    keys = [c["key"] for c in classified]
    counts = {k: keys.count(k) for k in ("positive", "negative", "neutral")}
    enriched = [
        {**h, "sentiment": c["key"], "confidence": c["score"]}
        for h, c in zip(headlines, classified, strict=True)
    ]

    return {
        "status": "success",
        "ticker": ticker.upper(),
        "sentiment_available": True,
        "news_count": len(headlines),
        "aggregate_sentiment": _aggregate_score(keys),
        "label_counts": counts,
        "headlines": enriched,
    }
