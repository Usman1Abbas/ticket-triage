# 🎫 ticket-triage

A RAG-backed support-ticket triage service that **classifies, prioritizes, and routes** incoming tickets using an LLM — returning clean, schema-validated decisions instead of free-form text.

## Why
Support teams drown in unstructured tickets. This service turns each raw ticket into a structured triage decision (category, priority, suggested route) an automated workflow or human agent can act on immediately.

## How it works
1. **Ingest** — ticket text arrives via a FastAPI endpoint.
2. **Retrieve** — relevant context (past tickets / knowledge base) is pulled from a **ChromaDB** vector store.
3. **Classify & triage** — an LLM (via **OpenRouter**) reasons over the ticket + retrieved context.
4. **Structure** — **Instructor + Pydantic** force the model's output into a validated schema — no brittle parsing.

## Tech stack
| Layer | Tools |
|---|---|
| API | FastAPI · Uvicorn · python-multipart |
| LLM | OpenAI / OpenRouter · Instructor (structured outputs) · tiktoken |
| Retrieval | ChromaDB (vector KB) |
| Validation | Pydantic v2 · pydantic-settings |
| Testing | pytest · pytest-asyncio |

## Project layout
```
backend/
  pipeline/    # classify.py, triage.py, openrouter.py — core triage logic
  models/      # schemas.py — Pydantic output contracts
  kb/          # ChromaDB knowledge-base layer
  db/          # persistence
  config.py    # settings
tests/         # pytest suite
```

## Running locally
```bash
cd backend
pip install -r requirements.txt
# set OPENROUTER_API_KEY in your environment / .env
uvicorn main:app --reload
```

## Status
Working prototype demonstrating structured-output LLM pipelines + retrieval. Part of my work on **agentic, production-minded AI systems**.
