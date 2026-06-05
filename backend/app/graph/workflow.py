"""
app/graph/workflow.py
LangGraph StateGraph wiring all five agents together.

Flow:
  START
    → intent_classifier
    → escalation_check         (conditional: escalate immediately if Human Escalation intent)
    → knowledge_retrieval      (skipped for escalation)
    → ticket_creation          (conditional: only for actionable intents)
    → escalation_evaluation    (check low-confidence / dissatisfaction post-RAG)
    → response_composer
  END
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.state import AgentState
from app.agents.intent_agent import run_intent_agent
from app.agents.knowledge_agent import run_knowledge_agent
from app.agents.ticket_agent import run_ticket_agent
from app.agents.escalation_agent import run_escalation_agent
from app.agents.response_agent import run_response_agent


# ── Sync wrappers (LangGraph nodes must be sync or async; we use async) ────────

async def _intent_node(state: AgentState) -> AgentState:
    """Classify user intent."""
    return run_intent_agent(state)


async def _knowledge_node(state: AgentState) -> AgentState:
    """Retrieve knowledge base answer."""
    return run_knowledge_agent(state)


async def _ticket_node(state: AgentState) -> AgentState:
    """Create ticket if needed."""
    return await run_ticket_agent(state)


async def _escalation_node(state: AgentState) -> AgentState:
    """Evaluate and execute escalation."""
    return await run_escalation_agent(state)


async def _response_node(state: AgentState) -> AgentState:
    """Compose final response."""
    return run_response_agent(state)


# ── Conditional routing ────────────────────────────────────────────────────────

def _route_after_intent(state: AgentState) -> str:
    """If user explicitly requests a human, skip RAG and go straight to escalation."""
    if state.get("intent") == "Human Escalation":
        return "escalation"
    return "knowledge"


def _route_after_knowledge(state: AgentState) -> str:
    """Always go to ticket creation after knowledge retrieval."""
    return "ticket"


def _route_after_ticket(state: AgentState) -> str:
    """Always evaluate escalation after ticket step."""
    return "escalation"


# ── Graph assembly ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("intent_classifier", _intent_node)
    graph.add_node("knowledge_retrieval", _knowledge_node)
    graph.add_node("ticket_creation", _ticket_node)
    graph.add_node("escalation_evaluation", _escalation_node)
    graph.add_node("response_composer", _response_node)

    # Edges
    graph.add_edge(START, "intent_classifier")

    graph.add_conditional_edges(
        "intent_classifier",
        _route_after_intent,
        {
            "knowledge": "knowledge_retrieval",
            "escalation": "escalation_evaluation",
        },
    )

    graph.add_edge("knowledge_retrieval", "ticket_creation")
    graph.add_edge("ticket_creation", "escalation_evaluation")
    graph.add_edge("escalation_evaluation", "response_composer")
    graph.add_edge("response_composer", END)

    return graph


@lru_cache(maxsize=1)
def get_compiled_graph():
    """Return a compiled, ready-to-invoke LangGraph app."""
    return build_graph().compile()
