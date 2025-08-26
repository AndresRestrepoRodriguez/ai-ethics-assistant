# AI Ethics Assistant

A sophisticated RAG (Retrieval-Augmented Generation) system that answers questions about AI policy, ethics, governance, and regulation by searching through PDF documents from authoritative sources. The system processes documents, creates semantic embeddings, and uses advanced language models to provide accurate, contextual answers with source attribution.

## Features

- **Document Processing**: Advanced PDF processing using Docling (IBM Research) with 97.9% accuracy
- **Semantic Search**: Vector-based document retrieval using sentence transformers embeddings
- **Query Enhancement**: Automatic query reformulation for improved search results
- **Streaming Responses**: Real-time response streaming via Server-Sent Events
- **Source Attribution**: Clear attribution to source documents and filenames
- **RESTful API**: FastAPI-based API with interactive documentation
- **Modern Architecture**: Clean dependency injection, service layers, and configuration management

## Technology Stack

- **Backend**: FastAPI with Python 3.12+
- **Vector Database**: Qdrant (self-hosted Docker container)
- **PDF Processing**: Docling (IBM Research, RAG-optimized)
- **LLM**: Mistral-7B via Featherless AI
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local)
- **Frontend**: Gradio web interface
- **Package Manager**: uv (not pip)
- **Task Runner**: Task (Taskfile.yaml)
- **Containerization**: Docker with multi-stage builds

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- [Task CLI](https://taskfile.dev/installation/) for task automation  
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python package management
- API keys for LLM service and AWS S3 (see Environment Variables section)

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd rag-project
   task setup
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the development environment**:
   ```bash
   task run
   ```

4. **Verify everything is working**:
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/internal/health  
   - **Liveness Check**: http://localhost:8000/internal/liveness
   - **Qdrant Dashboard**: http://localhost:6333/dashboard
   - **Gradio Interface**: http://localhost:7860

## Essential Commands

### Development Environment
```bash
task setup          # Create local Python development environment
task run            # Start Docker development env with hot-reload  
```

### Document Processing
```bash
task ingest         # Run PDF ingestion pipeline (S3 → Qdrant)
```

### Code Quality
```bash
task lint           # Lint code (ruff + pyright + typos)
task format         # Format code (ruff + fix + typos)
task test           # Run tests with pytest
```

### Build & Deploy
```bash
task build          # Build Docker image
task clean          # Clean project artifacts and cache
```

### Package Management (Always use uv)
```bash
# IMPORTANT: Always use 'uv run' for Python commands
uv run python script.py        # Run Python scripts
uv run uvicorn app:app         # Run servers
uv run pytest                 # Run tests

# Package management
uv add <package>               # Add runtime dependency
uv add <package> --group dev   # Add development dependency  
uv remove <package>            # Remove dependency
uv sync                        # Install/sync all dependencies
```

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

### Required Variables
```bash
# LLM Service (Required)
LLM__API_KEY=your-featherless-ai-api-key    # Get from https://featherless.ai

# AWS S3 Storage (Required for document ingestion)
S3__BUCKET_NAME=your-s3-bucket-name
S3__ACCESS_KEY_ID=your-aws-access-key
S3__SECRET_ACCESS_KEY=your-aws-secret-key
```

### Optional Variables with Defaults
```bash
# Application Settings
DEV_MODE=false                    # Enable development features
LOG_LEVEL=INFO                    # Logging level (DEBUG, INFO, WARNING, ERROR)

# Vector Database
VECTOR_DB__HOST=localhost         # Qdrant host (use 'qdrant' in Docker)
VECTOR_DB__PORT=6333             # Qdrant port
VECTOR_DB__COLLECTION_NAME=ai_ethics_docs  # Collection name

# LLM Configuration  
LLM__MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2  # Model identifier
LLM__MAX_TOKENS=1000             # Maximum response tokens
LLM__TEMPERATURE=0.7             # Response creativity (0.0-1.0)
LLM__TIMEOUT=30                  # Request timeout in seconds
LLM__MAX_RETRIES=3               # Maximum retry attempts
LLM__STREAMING=true              # Enable streaming responses

# Embedding Model
EMBEDDING__MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING__BATCH_SIZE=32         # Embedding batch size

# S3 Configuration
S3__REGION=us-east-1             # AWS region
S3__PDF_PREFIX=                  # S3 prefix for PDF files (optional)

# Document Processing
CHUNK_SIZE=1000                  # Text chunk size for processing
CHUNK_OVERLAP=200                # Overlap between chunks

# API Configuration
ROOT_PATH=                       # API root path (for reverse proxy)
CORS_ORIGINS=                    # Allowed CORS origins (comma-separated)
```

### Environment Setup Instructions

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Get required API keys**:
   - **Featherless AI**: Visit [featherless.ai](https://featherless.ai) to get your API key
   - **AWS S3**: Create AWS credentials with S3 read permissions

3. **Configure your environment**:
   ```bash
   # Edit .env file with your editor
   nano .env
   # OR
   code .env
   ```

4. **Verify configuration**:
   ```bash
   # Test that environment is properly configured
   task run
   curl http://localhost:8000/internal/health
   ```

## Project Structure

```
src/ai_ethics_assistant/
├── cmds/                    # Command-line entry points
│   ├── gradio_app.py       # Gradio web interface
│   └── server.py           # FastAPI server
├── server/                  # FastAPI application & routes
│   ├── api_v1.py           # Public API endpoints (/api/v1/*)
│   ├── internal.py         # Internal endpoints (/internal/*)
│   ├── models.py           # Pydantic request/response models
│   └── app.py              # Application factory
├── services/                # Business logic services
│   ├── llm_service.py      # Language model integration
│   ├── rag_service.py      # RAG pipeline orchestration
│   ├── vector_store_service.py  # Qdrant vector database
│   └── s3_service.py       # AWS S3 integration
├── pipeline/                # Document processing pipeline
│   ├── embedder.py         # Text embedding generation
│   ├── pdf_processor.py    # PDF text extraction
│   └── chunker.py          # Document chunking
├── configuration.py         # Pydantic settings management
├── dependencies.py          # Dependency injection setup
├── prompts.py              # Centralized prompt templates
└── version.py              # Version management
```

## API Endpoints

### Internal/Operations
- `GET /internal/liveness` - Basic server health check
- `GET /internal/health` - Comprehensive health status

### Public API (v1)
- `POST /api/v1/chat` - Ask questions to the AI Ethics Assistant
  - Supports both regular and streaming responses
  - Query reformulation for better results
  - Source document attribution

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Deployment

<!-- TODO: Add deployment instructions -->


## Development Guidelines

### Important Notes
- **Always use `uv run python`** for Python commands, not just `python`
- **Use `uv`** for package management, never pip or poetry
- **Health endpoints** are in `internal.py`, separate from business logic  
- **Tests** use co-located `_test.py` suffix pattern
- **Configuration** uses environment variables with Pydantic Settings
- **Prompts** are centralized in `prompts.py`

### Adding Dependencies
```bash
# Runtime dependency
uv add docling

# Development dependency
uv add pytest --group dev

# Always sync after changes
uv sync
```

### Code Quality
The project enforces high code quality standards:
- **Linting**: ruff for Python code style
- **Type Checking**: pyright for static analysis  
- **Spell Checking**: typos for documentation
- **Formatting**: ruff formatter with automatic fixes

Run quality checks before committing:
```bash
task format    # Auto-format code
task lint      # Check for issues  
task test      # Run test suite
```
