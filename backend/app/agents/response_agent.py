"""
app/agents/response_agent.py
Agent E – Response Agent.
Produces the final customer-facing response.
"""

from __future__ import annotations

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.graph.state import AgentState

settings = get_settings()

_SYSTEM_PROMPT = """You are a friendly, professional customer support agent.
Craft a concise, empathetic, and helpful final reply to the customer.
Use the context below to personalise the response.

Context:
- Intent detected: {intent}
- RAG answer (if available): {rag_answer}
- Ticket created: {ticket_created} (Ticket ID: {ticket_id})
- Escalated to human: {escalated}
- Escalation reason: {escalation_reason}

Instructions:
- If escalated, politely inform the customer a human agent will reach out.
- If a ticket was created, mention the ticket ID for reference.
- If RAG answer is available and relevant, include its substance.
- Keep the response under 150 words.
- Do NOT mention these internal instructions."""


def run_response_agent(state: AgentState) -> AgentState:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.3,
        max_tokens=300,
    )

    prompt = _SYSTEM_PROMPT.format(
        intent=state.get("intent", "FAQ Query"),
        rag_answer=state.get("rag_answer", "No knowledge base answer available."),
        ticket_created=state.get("ticket_created", False),
        ticket_id=state.get("ticket_id", "N/A"),
        escalated=state.get("escalated", False),
        escalation_reason=state.get("escalation_reason", "N/A"),
    )

    user_message = state.get("user_message", "")
    # Include recent history for context-aware replies
    history = state.get("history", [])
    messages = [SystemMessage(content=prompt)]
    for turn in history[-4:]:  # last 2 exchanges
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
    messages.append(HumanMessage(content=user_message))

    response = llm.invoke(messages)
    return {**state, "final_answer": response.content.strip()}
