import pytest
import os
import tempfile
from datetime import datetime
from backend.models.schemas import Ticket, TicketClassification, DraftReply, TicketTrace
from backend.db.sqlite import Database

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    database = Database(path)
    database.init()
    yield database
    # Close any lingering SQLite connections before deletion (needed on Windows)
    import sqlite3
    try:
        conn = sqlite3.connect(path)
        conn.close()
    except Exception:
        pass
    try:
        os.unlink(path)
    except PermissionError:
        pass  # Windows may hold the file briefly; skip cleanup

def test_insert_and_get_ticket(db):
    ticket = Ticket(subject="Help", body="I need help", sender_email="u@test.com")
    db.insert_ticket(ticket)
    result = db.get_ticket(ticket.id)
    assert result is not None
    assert result.id == ticket.id
    assert result.subject == "Help"
    assert result.status == "pending"

def test_list_tickets(db):
    for i in range(3):
        db.insert_ticket(Ticket(subject=f"T{i}", body="body", sender_email="u@test.com"))
    tickets = db.list_tickets()
    assert len(tickets) == 3

def test_update_ticket_status(db):
    ticket = Ticket(subject="T", body="b", sender_email="u@test.com")
    db.insert_ticket(ticket)
    db.update_ticket_status(ticket.id, "approved")
    result = db.get_ticket(ticket.id)
    assert result.status == "approved"

def test_metrics_empty(db):
    metrics = db.get_metrics()
    assert metrics.total_tickets == 0
    assert metrics.auto_draft_rate == 0.0
