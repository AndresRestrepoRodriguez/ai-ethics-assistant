# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Ethics Assistant - A RAG-based Q&A system for answering questions about AI policy and ethics from PDF documents. Uses Qdrant for vector storage, Hugging Face (Mistral-7B) for LLM, and FastAPI/Gradio for the interface.

## Essential Commands

```bash
# Package management (ALWAYS use uv, NEVER pip or poetry)
uv sync                        # Install all dependencies
uv add <package>              # Add runtime dependency
uv add <package> --group dev  # Add development dependency
uv remove <package>           # Remove runtime dependency
uv remove <package> --group dev # Remove development dependency

# Development
uv run uvicorn ai_ethics_assistant.cmds.server:app --reload --host 0.0.0.0  # Run API server
uv run python -m ai_ethics_assistant.cmds.gradio_app                        # Run Gradio UI
uv run python -m ai_ethics_assistant.cmds.ingest                           # Ingest PDFs

# Testing & Quality
uv run pytest                    # Run all tests
uv run pytest path/to/test.py   # Run specific test file
uv run pytest -k "test_name"    # Run specific test
uv run ruff format              # Format code
uv run ruff check              # Lint code
uv run pyright                 # Type check

# Docker
docker compose up -d          # Start services
docker compose up --watch     # Development with hot-reload
docker compose down          # Stop services
docker compose logs -f app   # View logs
```

## Architecture & Key Design Decisions

### RAG Pipeline Flow
1. **PDF Ingestion**: S3 → PDF Processor → Chunker → Embeddings → Qdrant
2. **Query Processing**: User Query → Embedding → Vector Search → Context Retrieval → LLM → Response

### Technology Stack
- **Vector DB**: Qdrant (self-hosted Docker container) - chosen for performance and self-hosting
- **PDF Processing**: Docling (IBM Research) - 97.9% accuracy, RAG-optimized, MIT license
- **LLM**: Mistral-7B via Hugging Face Inference API - free tier, no API key conflicts
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 - local, efficient
- **Backend**: FastAPI with dependency injection pattern
- **UI**: Gradio for rapid prototyping

### Code Organization Patterns
- **Repository Pattern**: Concrete base classes (not Protocols) in `repositories/`
- **Dependency Injection**: Constructor-based, no global state except logging
- **Configuration**: Pydantic Settings with `SecretStr` for sensitive values
- **Testing**: pytest with pytest-anyio for async tests, co-located as `*_test.py`
- **Type Hints**: Use built-in generics (`list`, `dict`), pipe operator for unions (`str | None`)

### Key Conventions (from conventions/)
- **Type hints**: Built-in types (`list`, `dict`), pipe operator (`str | None`), avoid dataclasses
- **Early returns**: For guard clauses and error conditions
- **Service layer**: Thin API controllers, business logic in services
- **Repository pattern**: Encapsulate all database operations
- **API structure**: Health endpoints in separate `internal.py` file
- **Testing**: Co-located tests with `_test.py` suffix
- **Documentation**: Detailed docstrings only for public APIs and entry points
- **Comments**: Explain WHY not WHAT, focus on business context

### Docker Setup
- Multi-stage builds: development, build, production stages
- Non-root user (`nobody`) in production
- Health checks configured for all services
- Volume mounts for Qdrant persistence
- Watch mode for development hot-reload

### Configuration Management
All config via environment variables, centralized in `configuration.py`:
- `VECTOR_DB__HOST`, `VECTOR_DB__PORT`: Qdrant connection
- `LLM__API_KEY`: Hugging Face API key (SecretStr)
- `S3__BUCKET_NAME`, `S3__ACCESS_KEY_ID`: AWS credentials
- `DEV_MODE`: Enable development features

### Current Implementation Status
- ✅ Project structure and configuration
- ✅ Docker setup (partial - needs Qdrant service)
- ✅ Architecture decisions (Docling for PDF processing)
- ⏳ Core implementation pending:
  - Docling integration (`pipeline/pdf_processor.py`)
  - RAG service (`services/rag_service.py`)
  - API endpoints (`server/api_v1.py`, `server/internal.py`)
  - Gradio interface (`cmds/gradio_app.py`)
  - Co-located tests for all components

## Git Conventions

### Commit Messages
Format: `<type>[!]: <description>` where type is:
- `feat`: New features or enhancements
- `fix`: Bug fixes
- `chore`: Maintenance, deps, docs, tests
- `refactor`: Code restructuring

Examples: `feat: add PDF ingestion pipeline`, `fix!: correct vector search logic`

### Branch Naming
Format: `<type>-<description>` or `<type>-<ticket>-<description>`
Examples: `feat-pdf-ingestion`, `fix-CON-123-search-accuracy`

## UV Usage Guidelines

**CRITICAL**: Always use `uv` for all Python operations:

```bash
# Python execution - ALWAYS use uv run
uv run python script.py        # NOT: python script.py
uv run python -m module        # NOT: python -m module
uv run uvicorn app:app         # NOT: uvicorn app:app
uv run pytest                 # NOT: pytest

# Package management - ALWAYS use uv
uv add package                 # NOT: pip install package
uv remove package             # NOT: pip uninstall package
uv sync                       # NOT: pip install -r requirements.txt
```

## Important Notes

1. **ALWAYS use `uv run` for all Python commands** - never call python/pytest/ruff directly
2. **ALWAYS use `uv add/remove` for package management** - never use pip or poetry
3. **Use Docling for PDF processing** - superior accuracy (97.9%) and RAG-optimized
4. **Health endpoints in `internal.py`** separate from business logic
5. **Co-located tests** with `_test.py` suffix, not separate test directories
6. **Use SecretStr** for all sensitive configuration values
7. **Test with pytest-anyio**, mark async tests with `@pytest.mark.anyio`
8. **Chunk size**: 1000-1500 chars with 200-300 char overlap for optimal retrieval
9. **Commit signing**: Use `-s` flag when committing

Refer to `ARCHITECTURE.md` for detailed design decisions and `conventions/` for complete coding standards.