# AI Ethics Assistant

 RAG system for AI policy and ethics Q&A, built with FastAPI, Qdrant, and Mistral-7B. Processes PDF documents via advanced semantic chunking and provides contextual answers with source attribution.

## System Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   S3 PDFs   │───▶│   Docling    │───▶│   Qdrant    │───▶│  Mistral-7B  │
│             │    │  Processing  │    │  VectorDB   │    │     LLM      │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                              │                    │
┌─────────────┐    ┌──────────────┐          │                    │
│   Gradio    │───▶│   FastAPI    │──────────┴────────────────────┘
│  Frontend   │    │   Backend    │
└─────────────┘    └──────────────┘
```

**Technology Stack**: FastAPI • Qdrant • Docling (97.9% accuracy) • Mistral-7B • sentence-transformers • Docker

**Performance**: ~2-5s response time • 1000-token chunks • Cosine similarity search

## Quick Start

### Local Development
```bash
# Prerequisites: Docker, uv, Task CLI
git clone <repo-url> && cd rag-project

# Environment setup
cp .env.example .env && nano .env  # Add API keys

# Development workflow
task setup          # Install dependencies and setup environment
task run             # Start with hot-reload (docker compose up --watch)

# Verify: http://localhost:7860 (Gradio) | http://localhost:8000/docs (API)
```

### Production Deployment (AWS)
```bash
# Infrastructure (Terraform)
cd deployment/terraform
cp terraform.tfvars.example terraform.tfvars && nano terraform.tfvars
terraform init && terraform apply

# Application deployment (on EC2)
ssh -i ~/.ssh/rag-assistant-key.pem ubuntu@<public-ip>
git clone <repo-url> /app && cd /app
docker compose up -d

# Ingestion pipeline
uv run --env-file=.env python scripts/ingest.py

# Access: http://<public-ip>
```

## Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM__API_KEY` | Featherless AI API key | - | ✅ |
| `S3__BUCKET_NAME` | S3 bucket with PDFs | - | ✅ |
| `S3__ACCESS_KEY_ID` | AWS access key | - | ✅ |
| `S3__SECRET_ACCESS_KEY` | AWS secret key | - | ✅ |
| `VECTOR_DB__HOST` | Qdrant host | `localhost` | - |
| `DEV_MODE` | Development features | `false` | - |

<details>
<summary>Complete configuration reference</summary>

```bash
# Application
DEV_MODE=false
LOG_LEVEL=INFO

# LLM Service
LLM__MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
LLM__MAX_TOKENS=1000
LLM__TEMPERATURE=0.7
LLM__STREAMING=true

# Vector Database
VECTOR_DB__HOST=localhost  # Use 'qdrant' in Docker
VECTOR_DB__PORT=6333
VECTOR_DB__COLLECTION_NAME=ai_ethics_docs

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING__MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```
</details>

## Development Workflow

```bash
# Setup
task setup                  # Create virtual environment and install dependencies

# Development
task run                    # Start Docker development env with hot-reload
task test                   # Run tests with pytest
task format                 # Code formatting (ruff + typos)
task lint                   # Linting (ruff + pyright + typos)

# Document ingestion
task ingest                 # Run PDF ingestion pipeline (S3 → Qdrant)

# Build & Deploy
task build                  # Build Docker image
task clean                  # Clean project artifacts
```

## Production Operations

### AWS Infrastructure (~$18/month)
- **EC2**: t3.small (2 vCPU, 2GB RAM) - $15/month
- **Storage**: 30GB EBS GP3 - $3/month
- **Networking**: Elastic IP, Security Groups
- **IAM**: S3 read-only access via instance role

### Monitoring & Health Checks
```bash
# Health endpoints
curl http://localhost:8000/internal/health     # Application health
curl http://localhost:6333/health              # Qdrant health

# Logs
docker compose logs -f                         # All services
docker compose logs app                        # API only

# Resource usage
docker stats                                   # Container resources
```


## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Q&A with streaming support |
| `/internal/health` | GET | Health check |
| `/docs` | GET | Interactive API docs |

**Request Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are key AI ethics principles?"}'
```

## Troubleshooting

**Common Issues**:
- **Module not found**: Ensure `PYTHONPATH=/app/src` when running outside Docker
- **Qdrant connection**: Use `localhost` for host execution, `qdrant` for Docker
- **S3 permissions**: Verify IAM role has `s3:GetObject` and `s3:ListBucket`
- **Memory errors**: Increase Docker memory limits or use t3.medium

**Performance Tuning**:
- Batch size: Increase `EMBEDDING__BATCH_SIZE` for faster ingestion
- Chunk parameters: Adjust `CHUNK_SIZE`/`CHUNK_OVERLAP` for accuracy vs speed
- LLM temperature: Lower for more consistent responses

## Architecture Decisions

- **Docling over PyPDF**: 97.9% vs 75% table extraction accuracy
- **Qdrant**: Production-ready with better performance scaling
- **Mistral-7B**: Balance of quality and cost for personal projects
- **FastAPI**: Modern async Python with automatic docs generation
- **Container-first**: Consistent development/production environments
