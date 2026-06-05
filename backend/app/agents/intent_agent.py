"""
app/agents/intent_agent.py
Agent A – Intent Classifier.
Uses Groq LLM to detect one of five intents.
"""

from __future__ import annotations

import json
import re

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.graph.state import AgentState

settings = get_settings()

_INTENTS = [
    "FAQ Query",
    "Technical Issue",
    "Refund Request",
    "Order Tracking",
    "Human Escalation",
]

_SYSTEM_PROMPT = f"""You are an intent classification model for a customer support system.
Classify the user message into EXACTLY ONE of the following intents:
{json.dumps(_INTENTS)}

Rules:
- "Human Escalation" if the user explicitly asks to speak with a human/agent/representative.
- "Refund Request" for any refund, return, money-back, chargeback request.
- "Order Tracking" for delivery status, shipping, where is my order.
- "Technical Issue" for bugs, errors, technical problems, app not working.
- "FAQ Query" for general questions, product info, how-to, pricing.

Respond with ONLY a JSON object:
{{"intent": "<one of the intents above>", "confidence": <0.0-1.0>}}
No extra text."""


def run_intent_agent(state: AgentState) -> AgentState:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.0,
        max_tokens=64,
    )

    message = state.get("user_message", "")
    response = llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]
    )

    raw = response.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(raw)
        intent = parsed.get("intent", "FAQ Query")
        confidence = float(parsed.get("confidence", 0.8))
    except (json.JSONDecodeError, ValueError):
        intent = "FAQ Query"
        confidence = 0.5

    if intent not in _INTENTS:
        intent = "FAQ Query"

    return {**state, "intent": intent, "intent_confidence": confidence}
