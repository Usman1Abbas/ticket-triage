from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
import uuid

TicketStatus = Literal["pending", "auto_drafted", "review_queue", "approved", "sent"]

class TicketClassification(BaseModel):
    category: Literal["billing", "technical", "complaint", "general"]
    urgency: Literal["urgent", "normal", "low"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class DraftReply(BaseModel):
    subject: str
    body: str
    tone: Literal["formal", "friendly", "apologetic"]
    confidence: float = Field(ge=0.0, le=1.0)
    kb_sources: list[str] = Field(default_factory=list)

class TicketTrace(BaseModel):
    classification_model: str
    draft_model: str
    classification_tokens: int = 0
    draft_tokens: int = 0
    classification_cost_usd: float = 0.0
    draft_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    retry_count: int = 0
    latency_ms: int = 0

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: f"t_{uuid.uuid4().hex[:8]}")
    subject: str
    body: str
    sender_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: TicketStatus = "pending"
    classification: TicketClassification | None = None
    draft: DraftReply | None = None
    trace: TicketTrace | None = None

class TicketCreate(BaseModel):
    subject: str
    body: str
    sender_email: str

class TicketListItem(BaseModel):
    id: str
    subject: str
    sender_email: str
    created_at: datetime
    status: TicketStatus
    category: str | None
    urgency: str | None
    classification_confidence: float | None
    draft_confidence: float | None
    total_cost_usd: float | None

class MetricsResponse(BaseModel):
    total_tickets: int
    auto_drafted: int
    review_queue: int
    approved: int
    auto_draft_rate: float
    avg_cost_usd: float
    total_cost_usd: float
    avg_latency_ms: float
    avg_retry_count: float
    cost_by_model: dict[str, float]
