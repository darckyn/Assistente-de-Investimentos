"""Configuracao central da aplicacao.

Le variaveis de ambiente (via .env) com pydantic-settings. Nenhum segredo fica
hardcoded. O design e model-agnostic: trocar ``ADK_MODEL`` permite usar Claude
(padrao), outro provedor LiteLLM, ou Ollama/Llama 3 totalmente offline.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Universo de acoes monitoradas (descritivo do projeto).
TICKERS: dict[str, str] = {
    "VALE3": "Vale do Rio Doce (Mineracao)",
    "PETR4": "Petrobras (Energia)",
    "BBAS3": "Banco do Brasil (Financeiro)",
    "ITUB4": "Itau Unibanco (Financeiro)",
}

# Feeds RSS de noticias financeiras (open source, sem API key).
NEWS_FEEDS: tuple[str, ...] = (
    "https://www.infomoney.com.br/feed/",
    "https://www.infomoney.com.br/mercados/feed/",
    "https://braziljournal.com/feed/",
    "https://valor.globo.com/rss/home/",
)

# Termos extras de busca por ticker, para casar noticias que nao citam o codigo.
TICKER_ALIASES: dict[str, tuple[str, ...]] = {
    "VALE3": ("vale", "minerio de ferro", "mineracao"),
    "PETR4": ("petrobras", "petroleo", "combustivel"),
    "BBAS3": ("banco do brasil", "bb "),
    "ITUB4": ("itau", "itau unibanco", "itausa"),
}


class Settings(BaseSettings):
    """Configuracoes carregadas de variaveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (formato de modelo LiteLLM). Confirme o nome atual do modelo Anthropic.
    adk_model: str = Field(default="anthropic/claude-sonnet-4-5")
    anthropic_api_key: str | None = Field(default=None)

    # Alternativa local/offline (Ollama).
    ollama_api_base: str | None = Field(default=None)

    # Modelo de analise de sentimento em portugues (FinBERT-PT-BR).
    sentiment_model: str = Field(default="lucas-leme/FinBERT-PT-BR")

    # Parametros default de coleta/analise.
    default_period: str = Field(default="6mo")
    news_lookback_days: int = Field(default=7)
    max_news_per_ticker: int = Field(default=15)

    # Identificacao da aplicacao ADK.
    app_name: str = Field(default="assistente_investimentos")


@lru_cache
def get_settings() -> Settings:
    """Retorna a instancia unica de Settings (cacheada)."""
    return Settings()
