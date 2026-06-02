"""Interface conversacional (Chainlit) do Assistente de Investimentos.

Conecta a UI ao Runner do ADK e faz streaming dos eventos do agente, tornando
visivel o raciocinio (chamadas de tools = Chain-of-Thought) e exibindo graficos
gerados pela tool `plot_chart`.

Execucao:
    poetry run chainlit run app.py -w
"""

from __future__ import annotations

from pathlib import Path

import chainlit as cl

from assistente.config import TICKERS
from assistente.runner import AgentSession

_WELCOME = (
    "### Assistente de Investimentos (B3)\n"
    "Analiso **" + ", ".join(TICKERS) + "** combinando indicadores tecnicos e "
    "sentimento de noticias, e recomendo **COMPRAR / VENDER / AGUARDAR** com o "
    "raciocinio explicado.\n\n"
    'Experimente: *"Analise a VALE3"* ou *"Por que comprar PETR4 hoje?"*\n\n'
    "> Analise automatizada para fins educacionais; nao constitui recomendacao "
    "formal de investimento."
)


@cl.on_chat_start
async def on_chat_start() -> None:
    cl.user_session.set("agent", AgentSession())
    await cl.Message(content=_WELCOME).send()


async def _handle_part(part) -> None:
    """Renderiza um trecho de evento: chamada de tool ou imagem de resposta."""
    if getattr(part, "function_call", None):
        fc = part.function_call
        async with cl.Step(name=fc.name, type="tool") as step:
            step.input = dict(fc.args or {})

    response = getattr(part, "function_response", None)
    if response is not None:
        payload = getattr(response, "response", None)
        if isinstance(payload, dict) and payload.get("image_path"):
            path = Path(payload["image_path"])
            if path.exists():
                await cl.Message(
                    content=f"Grafico de {payload.get('ticker', '')}",
                    elements=[cl.Image(path=str(path), name=path.name, display="inline")],
                ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    session: AgentSession = cl.user_session.get("agent")

    async for event in session.stream(message.content):
        parts = (event.content.parts if event.content else None) or []
        for part in parts:
            await _handle_part(part)

        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text or ""
            if text.strip():
                await cl.Message(content=text).send()
