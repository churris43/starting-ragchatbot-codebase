# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Quick start (from project root)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

Requires a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

App runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Installing Dependencies

```bash
uv sync
```

Always use `uv` to run Python commands and manage packages. Never use `pip` directly. Use `uv run python <file>` to run Python files.

## Architecture

This is a RAG (Retrieval-Augmented Generation) chatbot. The server runs from the `backend/` directory — all imports are relative to that directory (not the project root).

**Query flow:**
1. `POST /api/query` hits `app.py`
2. `RAGSystem.query()` builds a prompt and calls Claude via `AIGenerator`
3. Claude decides whether to call the `search_course_content` tool (defined in `search_tools.py`)
4. If tool is called, `ToolManager` dispatches to `CourseSearchTool`, which queries ChromaDB via `VectorStore`
5. ChromaDB results are returned to Claude, which synthesizes the final answer
6. Conversation history is appended to the session via `SessionManager`

**On startup**, course documents from `docs/` are loaded, chunked, embedded (using `all-MiniLM-L6-v2` via `sentence-transformers`), and stored in ChromaDB at `backend/chroma_db/`. Already-indexed courses are skipped.

**Two ChromaDB collections:**
- `course_catalog` — course-level metadata (title, instructor, lesson links)
- `course_content` — chunked course text for semantic search

**Key config values** (in `backend/config.py`):
- Model: `claude-sonnet-4-20250514`
- Chunk size: 800 chars, overlap: 100
- Max search results: 5
- Max conversation history: 2 exchanges

## Adding a New Tool

1. Subclass `Tool` in `search_tools.py`, implementing `get_tool_definition()` and `execute()`
2. Register it in `RAGSystem.__init__()` via `self.tool_manager.register_tool(...)`

Claude will automatically have access to it on the next query.
