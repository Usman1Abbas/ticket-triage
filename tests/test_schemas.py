import pytest
from pydantic import ValidationError
from backend.models.schemas import (
    TicketClassification, DraftReply, TicketTrace, Ticket
)

def test_ticket_classification_valid():
    c = TicketClassification(
        category="billing",
        urgency="urgent",
        confidence=0.95,
        reasoning="Mentions invoice and payment"
    )
    assert c.category == "billing"
    assert c.confidence == 0.95

def test_ticket_classification_invalid_category():
    with pytest.raises(ValidationError):
        TicketClassification(
            category="unknown",
            urgency="normal",
            confidence=0.8,
            reasoning="test"
        )

def test_ticket_classification_confidence_bounds():
    with pytest.raises(ValidationError):
        TicketClassification(
            category="billing",
            urgency="normal",
            confidence=1.5,
            reasoning="test"
        )

def test_draft_reply_valid():
    d = DraftReply(
        subject="Re: Invoice question",
        body="Thank you for reaching out...",
        tone="formal",
        confidence=0.85,
        kb_sources=["doc_1", "doc_2"]
    )
    assert d.tone == "formal"
    assert len(d.kb_sources) == 2

def test_ticket_defaults():
    t = Ticket(
        subject="Help",
        body="I need help",
        sender_email="user@example.com"
    )
    assert t.status == "pending"
    assert t.classification is None
    assert t.draft is None
    assert t.trace is None
