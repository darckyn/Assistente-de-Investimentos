"""Interface de linha de comando do Assistente de Investimentos.

Uso:
    poetry run assistente VALE3
    poetry run assistente "Por que comprar PETR4 hoje?"
    poetry run assistente            # modo interativo (REPL)
"""

from __future__ import annotations

import asyncio
import sys

from assistente.runner import AgentSession


def _format_event(event) -> str | None:
    """Resume um evento do ADK para exibicao do raciocinio (Chain-of-Thought)."""
    parts = getattr(getattr(event, "content", None), "parts", None) or []
    lines: list[str] = []
    for part in parts:
        if getattr(part, "function_call", None):
            fc = part.function_call
            lines.append(f"  -> chamando tool: {fc.name}({dict(fc.args or {})})")
        elif getattr(part, "function_response", None):
            lines.append(f"  <- resposta da tool: {part.function_response.name}")
    return "\n".join(lines) if lines else None


async def _run(message: str) -> None:
    session = AgentSession()
    print(f"\n[Pergunta] {message}\n" + "-" * 60)
    async for event in session.stream(message):
        trace = _format_event(event)
        if trace:
            print(trace)
        if event.is_final_response() and event.content and event.content.parts:
            print("-" * 60)
            print(event.content.parts[0].text)


async def _repl() -> None:
    session = AgentSession()
    print("Assistente de Investimentos (digite 'sair' para encerrar).")
    while True:
        try:
            message = input("\nvoce> ").strip()
        except EOFError, KeyboardInterrupt:
            break
        if message.lower() in {"sair", "exit", "quit"}:
            break
        if not message:
            continue
        async for event in session.stream(message):
            if event.is_final_response() and event.content and event.content.parts:
                print(f"\nassistente> {event.content.parts[0].text}")


def main() -> None:
    """Ponto de entrada (script `assistente`)."""
    args = sys.argv[1:]
    if args:
        asyncio.run(_run(" ".join(args)))
    else:
        asyncio.run(_repl())


if __name__ == "__main__":
    main()
