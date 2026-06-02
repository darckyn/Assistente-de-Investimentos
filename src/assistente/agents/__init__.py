"""Agentes do Assistente de Investimentos (Google ADK).

Arquitetura multi-agente: um agente tecnico e um agente de noticias (sub-agentes),
coordenados por um orquestrador que toma a decisao final com Chain-of-Thought.
"""

from assistente.agents.orchestrator import build_root_agent

__all__ = ["build_root_agent"]
