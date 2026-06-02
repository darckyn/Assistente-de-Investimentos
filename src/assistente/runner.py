"""Infraestrutura de execucao do agente (ADK Runner + SessionService).

Centraliza a criacao do Runner e o streaming de eventos, reutilizado pela CLI e
pela interface Chainlit.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from assistente.agents import build_root_agent
from assistente.config import get_settings


class AgentSession:
    """Encapsula um Runner ADK e uma sessao de conversa.

    Mantem o estado entre mensagens (memoria de curto prazo da conversa), o que
    permite perguntas de acompanhamento como "e a PETR4?".
    """

    def __init__(self, agent: LlmAgent | None = None, user_id: str = "local-user") -> None:
        settings = get_settings()
        self._app_name = settings.app_name
        self._user_id = user_id
        self._session_id = uuid.uuid4().hex
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=agent or build_root_agent(),
            app_name=self._app_name,
            session_service=self._session_service,
        )
        self._started = False

    async def _ensure_session(self) -> None:
        if not self._started:
            await self._session_service.create_session(
                app_name=self._app_name,
                user_id=self._user_id,
                session_id=self._session_id,
            )
            self._started = True

    async def stream(self, message: str) -> AsyncIterator:
        """Envia uma mensagem e itera sobre os eventos do agente (em tempo real)."""
        await self._ensure_session()
        content = types.Content(role="user", parts=[types.Part(text=message)])
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=self._session_id,
            new_message=content,
        ):
            yield event

    async def ask(self, message: str) -> str:
        """Envia uma mensagem e retorna apenas o texto da resposta final."""
        final_text = ""
        async for event in self.stream(message):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""
        return final_text
