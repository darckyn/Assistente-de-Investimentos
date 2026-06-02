"""Coleta de noticias financeiras via RSS (feedparser).

``search_news`` busca, nos feeds configurados, manchetes relacionadas a um ticker
(pelo codigo ou por apelidos da empresa) dentro de uma janela de dias.
"""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import UTC, datetime, timedelta

import feedparser

from assistente.config import NEWS_FEEDS, TICKER_ALIASES, get_settings

_HTML_TAG = re.compile(r"<[^>]+>")


def _normalize(text: str) -> str:
    """Minusculas sem acentos, para casamento robusto de termos."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _clean_summary(raw: str, limit: int = 400) -> str:
    text = _HTML_TAG.sub("", raw or "").strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def _entry_datetime(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed is None:
        return None
    return datetime.fromtimestamp(time.mktime(parsed), tz=UTC)


def _search_terms(ticker: str) -> list[str]:
    t = ticker.strip().upper()
    terms = [t, t[:4]]  # codigo completo e nome base (ex.: VALE3 -> VALE)
    terms.extend(TICKER_ALIASES.get(t, ()))
    return [_normalize(term) for term in terms if term]


def search_news(ticker: str, max_items: int = 0, lookback_days: int = 0) -> dict:
    """Busca noticias financeiras recentes relacionadas a uma acao da B3.

    Args:
        ticker: Codigo da acao (ex.: "PETR4").
        max_items: Maximo de noticias a retornar (0 = usar o default da config).
        lookback_days: Janela em dias (0 = usar o default da config).

    Returns:
        dict com status e uma lista de noticias (title, summary, link, published).
    """
    settings = get_settings()
    max_items = max_items or settings.max_news_per_ticker
    lookback_days = lookback_days or settings.news_lookback_days

    try:
        terms = _search_terms(ticker)
        cutoff = datetime.now(tz=UTC) - timedelta(days=lookback_days)
        seen_titles: set[str] = set()
        items: list[dict] = []

        for feed_url in NEWS_FEEDS:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                haystack = _normalize(f"{title} {summary}")
                if not any(term in haystack for term in terms):
                    continue

                published = _entry_datetime(entry)
                if published is not None and published < cutoff:
                    continue

                key = _normalize(title)
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                items.append(
                    {
                        "title": title.strip(),
                        "summary": _clean_summary(summary),
                        "link": getattr(entry, "link", ""),
                        "published": published.strftime("%Y-%m-%d %H:%M") if published else None,
                    }
                )

        items.sort(key=lambda x: x["published"] or "", reverse=True)
        items = items[:max_items]

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "count": len(items),
            "lookback_days": lookback_days,
            "news": items,
        }
    except Exception as exc:
        return {"status": "error", "error_message": f"Falha ao buscar noticias de {ticker}: {exc}"}
