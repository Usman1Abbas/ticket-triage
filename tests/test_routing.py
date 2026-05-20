import pytest
from backend.models.schemas import TicketClassification, DraftReply
from backend.pipeline.triage import should_route_to_review

def test_high_confidence_auto_drafted():
    classification = TicketClassification(
        category="billing", urgency="normal", confidence=0.90, reasoning="clear"
    )
    draft = DraftReply(
        subject="Re", body="body", tone="formal", confidence=0.85, kb_sources=[]
    )
    assert should_route_to_review(classification, draft) is False

def test_low_classification_confidence_routes_to_review():
    classification = TicketClassification(
        category="billing", urgency="normal", confidence=0.50, reasoning="unclear"
    )
    draft = DraftReply(
        subject="Re", body="body", tone="formal", confidence=0.85, kb_sources=[]
    )
    assert should_route_to_review(classification, draft) is True

def test_low_draft_confidence_routes_to_review():
    classification = TicketClassification(
        category="billing", urgency="normal", confidence=0.90, reasoning="clear"
    )
    draft = DraftReply(
        subject="Re", body="body", tone="formal", confidence=0.40, kb_sources=[]
    )
    assert should_route_to_review(classification, draft) is True

def test_zero_confidence_routes_to_review():
    classification = TicketClassification(
        category="general", urgency="low", confidence=0.0, reasoning=""
    )
    draft = DraftReply(
        subject="", body="x", tone="formal", confidence=0.0, kb_sources=[]
    )
    assert should_route_to_review(classification, draft) is True

def test_exactly_at_threshold_auto_drafted():
    classification = TicketClassification(
        category="billing", urgency="normal", confidence=0.70, reasoning="ok"
    )
    draft = DraftReply(
        subject="Re", body="body", tone="formal", confidence=0.70, kb_sources=[]
    )
    assert should_route_to_review(classification, draft) is False
