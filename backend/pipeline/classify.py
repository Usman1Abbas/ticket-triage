from backend.models.schemas import Ticket, TicketClassification
from backend.pipeline.openrouter import llm_call
from backend.config import settings

CLASSIFY_SYSTEM = """You are a support ticket classifier. Analyze the ticket and return a structured classification.

Categories:
- billing: payment, invoice, refund, pricing, subscription issues
- technical: bugs, errors, setup, integration, API, performance issues
- complaint: service dissatisfaction, negative feedback, escalations, threats to cancel
- general: questions, feature requests, general inquiries, onboarding

Urgency:
- urgent: service down, payment failed, data loss, security breach, legal threats
- normal: standard issues requiring timely attention
- low: general questions, feature requests, minor annoyances

Set confidence (0.0-1.0) based on how certain you are. Use < 0.7 when the ticket is ambiguous."""


def build_classify_messages(ticket: Ticket) -> list[dict]:
    return [
        {"role": "system", "content": CLASSIFY_SYSTEM},
        {"role": "user", "content": f"Subject: {ticket.subject}\n\nBody: {ticket.body}"}
    ]


async def classify_ticket(
    ticket: Ticket,
) -> tuple[TicketClassification, int, int, float, int]:
    """
    Returns (classification, input_tokens, output_tokens, cost_usd, retry_count).
    Falls back to a low-confidence 'general' classification on any error.
    """
    messages = build_classify_messages(ticket)
    try:
        result, input_tokens, output_tokens, cost = await llm_call(
            model=settings.classification_model,
            messages=messages,
            response_model=TicketClassification,
            max_retries=settings.max_retries,
        )
        return result, input_tokens, output_tokens, cost, 0
    except Exception:
        fallback = TicketClassification(
            category="general",
            urgency="normal",
            confidence=0.0,
            reasoning="Classification failed after retries"
        )
        return fallback, 0, 0, 0.0, settings.max_retries
