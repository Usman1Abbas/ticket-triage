import sqlite3
import json
from datetime import datetime
from backend.models.schemas import (
    Ticket, TicketClassification, DraftReply, TicketTrace,
    TicketListItem, MetricsResponse, TicketStatus
)


class Database:
    def __init__(self, path: str = "./tickets.db"):
        self.path = path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    sender_email TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    category TEXT,
                    urgency TEXT,
                    classification_confidence REAL,
                    classification_reasoning TEXT,
                    draft_subject TEXT,
                    draft_body TEXT,
                    draft_tone TEXT,
                    draft_confidence REAL,
                    kb_sources TEXT,
                    classification_model TEXT,
                    draft_model TEXT,
                    classification_tokens INTEGER DEFAULT 0,
                    draft_tokens INTEGER DEFAULT 0,
                    classification_cost_usd REAL DEFAULT 0,
                    draft_cost_usd REAL DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def insert_ticket(self, ticket: Ticket):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO tickets (id, subject, body, sender_email, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                ticket.id, ticket.subject, ticket.body,
                ticket.sender_email, ticket.created_at.isoformat(), ticket.status
            ))
            conn.commit()

    def update_ticket(self, ticket: Ticket):
        # Caller must pass a fully-hydrated Ticket — any None nested object will NULL
        # out that group's columns. Always re-fetch from DB before calling if in doubt.
        c = ticket.classification
        d = ticket.draft
        tr = ticket.trace
        with self._conn() as conn:
            conn.execute("""
                UPDATE tickets SET
                    status=?, category=?, urgency=?,
                    classification_confidence=?, classification_reasoning=?,
                    draft_subject=?, draft_body=?, draft_tone=?,
                    draft_confidence=?, kb_sources=?,
                    classification_model=?, draft_model=?,
                    classification_tokens=?, draft_tokens=?,
                    classification_cost_usd=?, draft_cost_usd=?,
                    total_cost_usd=?, retry_count=?, latency_ms=?
                WHERE id=?
            """, (
                ticket.status,
                c.category if c else None,
                c.urgency if c else None,
                c.confidence if c else None,
                c.reasoning if c else None,
                d.subject if d else None,
                d.body if d else None,
                d.tone if d else None,
                d.confidence if d else None,
                json.dumps(d.kb_sources) if d else None,
                tr.classification_model if tr else None,
                tr.draft_model if tr else None,
                tr.classification_tokens if tr else 0,
                tr.draft_tokens if tr else 0,
                tr.classification_cost_usd if tr else 0,
                tr.draft_cost_usd if tr else 0,
                tr.total_cost_usd if tr else 0,
                tr.retry_count if tr else 0,
                tr.latency_ms if tr else 0,
                ticket.id
            ))
            conn.commit()

    def update_ticket_status(self, ticket_id: str, status: TicketStatus):
        with self._conn() as conn:
            conn.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
            conn.commit()

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if not row:
            return None
        return self._row_to_ticket(row)

    def list_tickets(self, status: str | None = None) -> list[TicketListItem]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tickets WHERE status=? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tickets ORDER BY created_at DESC"
                ).fetchall()
        return [self._row_to_list_item(r) for r in rows]

    def get_metrics(self) -> MetricsResponse:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='auto_drafted' THEN 1 ELSE 0 END) as auto_drafted,
                    SUM(CASE WHEN status='review_queue' THEN 1 ELSE 0 END) as review_queue,
                    SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) as approved,
                    AVG(total_cost_usd) as avg_cost,
                    SUM(total_cost_usd) as total_cost,
                    AVG(latency_ms) as avg_latency,
                    AVG(retry_count) as avg_retries
                FROM tickets WHERE status != 'pending'
            """).fetchone()

            model_rows = conn.execute("""
                SELECT model, SUM(cost) as total_cost FROM (
                    SELECT classification_model as model, classification_cost_usd as cost
                    FROM tickets WHERE classification_model IS NOT NULL
                    UNION ALL
                    SELECT draft_model as model, draft_cost_usd as cost
                    FROM tickets WHERE draft_model IS NOT NULL
                ) GROUP BY model
            """).fetchall()

        total = row["total"] or 0
        auto_drafted = row["auto_drafted"] or 0
        cost_by_model = {r["model"]: round(r["total_cost"] or 0, 6) for r in model_rows}

        return MetricsResponse(
            total_tickets=total,
            auto_drafted=auto_drafted,
            review_queue=row["review_queue"] or 0,
            approved=row["approved"] or 0,
            auto_draft_rate=round(auto_drafted / total, 3) if total > 0 else 0.0,
            avg_cost_usd=round(row["avg_cost"] or 0, 6),
            total_cost_usd=round(row["total_cost"] or 0, 6),
            avg_latency_ms=round(row["avg_latency"] or 0, 1),
            avg_retry_count=round(row["avg_retries"] or 0, 2),
            cost_by_model=cost_by_model,
        )

    def _row_to_ticket(self, row: sqlite3.Row) -> Ticket:
        classification = None
        if row["category"]:
            classification = TicketClassification(
                category=row["category"],
                urgency=row["urgency"],
                confidence=row["classification_confidence"],
                reasoning=row["classification_reasoning"] or ""
            )
        draft = None
        if row["draft_body"]:
            draft = DraftReply(
                subject=row["draft_subject"] or "",
                body=row["draft_body"],
                tone=row["draft_tone"] or "formal",
                confidence=row["draft_confidence"] or 0.0,
                kb_sources=json.loads(row["kb_sources"]) if row["kb_sources"] else []
            )
        trace = None
        if row["classification_model"]:
            trace = TicketTrace(
                classification_model=row["classification_model"],
                draft_model=row["draft_model"] or "",
                classification_tokens=row["classification_tokens"] or 0,
                draft_tokens=row["draft_tokens"] or 0,
                classification_cost_usd=row["classification_cost_usd"] or 0,
                draft_cost_usd=row["draft_cost_usd"] or 0,
                total_cost_usd=row["total_cost_usd"] or 0,
                retry_count=row["retry_count"] or 0,
                latency_ms=row["latency_ms"] or 0,
            )
        return Ticket(
            id=row["id"],
            subject=row["subject"],
            body=row["body"],
            sender_email=row["sender_email"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            classification=classification,
            draft=draft,
            trace=trace,
        )

    def _row_to_list_item(self, row: sqlite3.Row) -> TicketListItem:
        return TicketListItem(
            id=row["id"],
            subject=row["subject"],
            sender_email=row["sender_email"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
            category=row["category"],
            urgency=row["urgency"],
            classification_confidence=row["classification_confidence"],
            draft_confidence=row["draft_confidence"],
            total_cost_usd=row["total_cost_usd"],
        )
