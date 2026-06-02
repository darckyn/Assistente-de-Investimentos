"""Agente de Noticias e Sentimento.

Coleta noticias financeiras recentes de uma acao e avalia o sentimento de
mercado (apoiado pelo FinBERT-PT-BR quando disponivel).
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from assistente.config import get_settings
from assistente.tools.sentiment import analyze_news_sentiment

_INSTRUCTION = """\
Voce e um analista de noticias do mercado financeiro brasileiro. Sua tarefa e
avaliar o SENTIMENTO recente em torno de UMA acao da B3.

Procedimento (raciocine passo a passo):
1. Use `analyze_news_sentiment` para obter as manchetes recentes e o score de
   sentimento.
2. Se `sentiment_available` for true, use o score agregado e as classes
   (positive/negative/neutral) do FinBERT-PT-BR como base.
3. Se `sentiment_available` for false, avalie voce mesmo o tom das manchetes.
4. Resuma os 2-3 eventos mais relevantes e seu provavel impacto no papel.
5. Conclua com um vies de noticias: POSITIVO, NEGATIVO ou NEUTRO.

Responda em portugues, de forma concisa, com o raciocinio visivel. Se nao houver
noticias recentes, diga isso claramente e classifique como NEUTRO.
"""


def build_news_agent() -> LlmAgent:
    settings = get_settings()
    return LlmAgent(
        name="news_agent",
        model=LiteLlm(model=settings.adk_model),
        description="Analista de noticias: avalia o sentimento de mercado de uma acao da B3.",
        instruction=_INSTRUCTION,
        tools=[analyze_news_sentiment],
    )
