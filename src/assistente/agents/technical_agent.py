"""Agente de Analise Tecnica.

Interpreta indicadores graficos (RSI, MACD, SMA/EMA, Bandas de Bollinger, volume)
de uma acao e resume o quadro tecnico de forma objetiva.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from assistente.config import get_settings
from assistente.tools.indicators import calculate_indicators
from assistente.tools.market_data import get_price_data

_INSTRUCTION = """\
Voce e um analista tecnico de acoes da B3. Sua tarefa e avaliar o quadro
GRAFICO de UMA acao, sem opinar sobre noticias.

Procedimento (raciocine passo a passo):
1. Use `get_price_data` para obter o contexto de preco/volume do periodo.
2. Use `calculate_indicators` para obter RSI, MACD, SMA/EMA, Bandas de Bollinger
   e volume.
3. Interprete cada indicador explicitamente:
   - RSI: sobrecomprado (>=70), sobrevendido (<=30) ou neutro.
   - MACD: cruzamento bullish/bearish e forca do histograma.
   - Medias (SMA20 vs SMA50, EMA9 vs EMA21): tendencia de alta/baixa.
   - Bandas de Bollinger: posicao do preco (proximo da banda superior/inferior).
   - Volume: confirma ou nao o movimento.
4. Conclua com um vies tecnico: ALTA, BAIXA ou NEUTRO, e a forca da conviccao.

Responda em portugues, de forma concisa, deixando o raciocinio visivel. NAO
invente numeros: use apenas os valores retornados pelas tools.
"""


def build_technical_agent() -> LlmAgent:
    settings = get_settings()
    return LlmAgent(
        name="technical_agent",
        model=LiteLlm(model=settings.adk_model),
        description="Analista tecnico: interpreta indicadores graficos de uma acao da B3.",
        instruction=_INSTRUCTION,
        tools=[get_price_data, calculate_indicators],
    )
