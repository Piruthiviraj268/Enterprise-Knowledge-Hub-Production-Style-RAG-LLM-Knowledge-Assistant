# Enterprise Knowledge Hub Pro

Portfolio-grade local-first RAG platform: document ingestion, SQLite persistence, hybrid TF-IDF + lexical retrieval, citation-grounded answers, optional OpenAI generation with a faithfulness gate, conversation memory, CLI, HTTP API, evaluation harness, tests, and a polished browser UI.

## Quick start

Windows: run `run.bat`.

macOS/Linux:

```bash
./run.sh
```

Then open `http://127.0.0.1:8000`.

Manual setup:

```bash
python -m venv .venv
# activate it
pip install -r requirements.txt
cp .env.example .env
python -m khub.cli seed
python -m khub.server
```

## Optional OpenAI mode

Put your own key in `.env` as `OPENAI_API_KEY=...`. The project never hard-codes or logs API keys. The key pasted into the chat was intentionally NOT packaged; because it was exposed in a chat, rotate/revoke it before real use.

Without a key, the app remains fully usable using local extractive RAG.

## Features

- PDF, DOCX, TXT, Markdown and CSV ingestion.
- Sentence-aware overlapping chunking.
- SQLite document/chunk/conversation/message persistence.
- Hybrid retrieval: TF-IDF n-grams + lexical term overlap + phrase boost.
- Evidence threshold and abstention.
- Optional OpenAI generation constrained to retrieved context.
- Citation validation and sentence-level lexical faithfulness gate.
- Conversation history.
- CLI: seed, ingest, ask, search, stats, reindex, doctor.
- HTTP API with upload limits, auth token support, rate limiting and health checks.
- Evaluation benchmark under `eval/`.
- Unit/integration tests under `tests/`.

## API

`GET /api/health`, `GET /api/stats`, `GET /api/config`, `GET /api/documents`, `POST /api/documents`, `DELETE /api/documents/{id}`, `POST /api/search`, `POST /api/chat`, `POST /api/reindex`.

## Architecture

Browser / CLI → HTTP API → ingestion + retrieval + RAG service → SQLite.

Retrieval is deliberately local-first. The hosted LLM is an optional generation layer, not the source of truth. The source documents remain the evidence layer.

## Tests

```bash
python -m unittest discover -s tests -v
python -m eval.run_eval
```
