"""Agente Orquestrador (root).

Coordena o agente tecnico e o agente de noticias (como tools), consulta a
recomendacao baseline deterministica e toma a decisao final
(COMPRAR / VENDER / AGUARDAR) registrando o Chain-of-Thought.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from assistente.agents.news_agent import build_news_agent
from assistente.agents.technical_agent import build_technical_agent
from assistente.config import TICKERS, get_settings
from assistente.tools.charting import plot_chart
from assistente.tools.recommendation import generate_recommendation

_INSTRUCTION = f"""\
Voce e o Assistente de Investimentos da QuantumFinance, um agente que recomenda
operacoes em acoes da B3 de forma autonoma e EXPLICAVEL. Acoes monitoradas:
{", ".join(TICKERS)}.

Estrategia ReAct: raciocine e aja em passos, deixando o raciocinio
(Chain-of-Thought) sempre visivel para o usuario.

Para CADA pedido de recomendacao sobre uma acao:
1. Chame `technical_agent` para obter a leitura tecnica (indicadores graficos).
2. Chame `news_agent` para obter o sentimento das noticias recentes.
3. Chame `generate_recommendation` para obter o score quantitativo baseline
   (combinacao deterministica de indicadores + sentimento).
4. Concilie as tres fontes. Se houver divergencia (ex.: tecnico positivo, noticias
   negativas), explique como pesou cada lado.
5. Emita a decisao final em UMA das categorias: COMPRAR, VENDER ou AGUARDAR.
6. Use `plot_chart` apenas se o usuario pedir um grafico.

Formato da resposta final (em portugues):
- **Raciocinio**: passo a passo, citando os numeros/sinais que fundamentaram a
  decisao (tecnico, sentimento e score baseline).
- **Recomendacao**: COMPRAR / VENDER / AGUARDAR.
- **Justificativa**: 2-3 frases resumindo o porque, em linguagem natural.

Regras:
- Responda perguntas como "Por que voce recomendou comprar PETR4 hoje?" recuperando
  e explicando o raciocinio.
- NAO invente dados: use somente o que as tools retornarem.
- Deixe claro que isto e analise automatizada e NAO constitui recomendacao formal
  de investimento.
"""


def build_root_agent() -> LlmAgent:
    """Constroi o agente orquestrador (root) com os sub-agentes como tools."""
    settings = get_settings()
    technical_agent = build_technical_agent()
    news_agent = build_news_agent()

    return LlmAgent(
        name="investment_orchestrator",
        model=LiteLlm(model=settings.adk_model),
        description="Orquestrador que decide COMPRAR/VENDER/AGUARDAR para acoes da B3.",
        instruction=_INSTRUCTION,
        tools=[
            AgentTool(agent=technical_agent),
            AgentTool(agent=news_agent),
            generate_recommendation,
            plot_chart,
        ],
    )
