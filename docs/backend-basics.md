# Hey.sh Backend - Basics

**Stage 0**: Getting started with the hey.sh backend orchestration layer.

## Overview

The hey.sh backend is built following Kenneth Pernyer's architectural conventions:

- **Singular directory structure** (`./workflow`, `./activity`, not plurals)
- **Temporal workflows** for orchestration
- **Neo4j** for knowledge graph
- **Weaviate** for vector search
- **FastAPI** for REST API
- **Prompts-as-code** system

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [just](https://github.com/casey/just) - Command runner

### Installation

```bash
cd backend

# Install dependencies
just bootstrap

# Start development environment
just dev
```

This will start:
- **Temporal server** + UI (http://localhost:8080)
- **Neo4j** browser (http://localhost:7474) - neo4j/password
- **Weaviate** (http://localhost:8081)
- **PostgreSQL** (for Temporal)
- **FastAPI backend** (http://localhost:8000)

## Architecture

### Directory Structure

```
backend/
├── workflow/         # Temporal workflow definitions
├── activity/         # Temporal activities
├── worker/          # Temporal workers
├── service/         # FastAPI services
├── src/app/         # Shared application code
│   ├── clients/       # Database/API clients
│   ├── models/        # Data models
│   ├── schemas/       # Pydantic schemas
│   └── utils/         # Utilities
├── prompt/          # Prompts-as-code
│   ├── coding/        # *.prompt.md
│   └── api-calling/   # *.prompt.yaml
├── tool/            # Development tools
├── script/          # Executable scripts
├── test/            # Tests
├── infra/           # Infrastructure as code
└── docker/          # Docker configurations
```

### Import Dependency Rules

**Critical architectural constraint:**

- ✅ `workflow`, `activity`, `worker`, `service` **MAY** import from `src/app/**`
- ❌ `src/app/**` **MUST NOT** import from `workflow`, `activity`, `worker`, `service`

This ensures core application logic remains independent of orchestration layers.

## Core Workflows

### 1. Document Processing Workflow

Orchestrates the full document processing pipeline:

```python
from temporalio.client import Client

client = await Client.connect("localhost:7233")

handle = await client.start_workflow(
    "DocumentProcessingWorkflow",
    args=["doc-123", "domain-456", "path/to/file.pdf"],
    id="doc-123",
    task_queue="hey-sh-workflows",
)

result = await handle.result()
```

**Steps:**
1. Download document from Supabase Storage
2. Extract text content
3. Generate embeddings
4. Index in Weaviate
5. Update Neo4j knowledge graph
6. Update document metadata

### 2. Question Answering Workflow

Handles user questions using the knowledge base:

```python
handle = await client.start_workflow(
    "QuestionAnsweringWorkflow",
    args=[
        "question-789",
        "What is Temporal?",
        "domain-456",
        "user-012",
    ],
    id="question-789",
    task_queue="hey-sh-workflows",
)

result = await handle.result()
```

**Steps:**
1. Vector search in Weaviate
2. Graph traversal in Neo4j
3. Generate answer using LLM
4. Calculate confidence score
5. Create review task if confidence < 0.7

### 3. Quality Review Workflow

Manages human-in-the-loop review processes:

```python
handle = await client.start_workflow(
    "QualityReviewWorkflow",
    args=[
        "review-345",
        "document",  # or "answer"
        "doc-123",
        "domain-456",
    ],
    id="review-345",
    task_queue="hey-sh-workflows",
)
```

## REST API Endpoints

The FastAPI service exposes these endpoints:

### Upload Document

```bash
POST /api/v1/documents
Content-Type: application/json

{
  "document_id": "doc-123",
  "domain_id": "domain-456",
  "file_path": "domain-456/document-123.pdf"
}
```

### Ask Question

```bash
POST /api/v1/questions
Content-Type: application/json

{
  "question_id": "q-789",
  "question": "What is Temporal?",
  "domain_id": "domain-456",
  "user_id": "user-012"
}
```

### Get Workflow Status

```bash
GET /api/v1/workflows/{workflow_id}
```

## Prompts-as-Code

### API-Calling Prompts

Located in `prompt/api-calling/*.prompt.yaml`:

```yaml
version: 1
model: claude-3-5-sonnet-20250219
temperature: 0.3
max_tokens: 2000

system: |
  You are a helpful assistant...

user_template: |
  Question: {{ question }}
  Context: {{ context }}
```

Render with variables:

```bash
just render-prompt prompt/api-calling/question-answering.v1.prompt.yaml \
  '{"question":"What is X?","context":[]}'
```

### Coding Prompts

Located in `prompt/coding/*.prompt.md`:

```markdown
---
id: add-workflow
version: 1
audience: "Claude|Cursor"
purpose: "Create new Temporal workflow"
---

# Template content here...
```

Use with Claude Code or Cursor AI.

## Database Clients

### Weaviate (Vector Search)

```python
from src.app.clients.weaviate import get_weaviate_client

weaviate = get_weaviate_client()
results = await weaviate.search(
    collection="Documents",
    query="What is Temporal?",
    filters={"domain_id": "domain-456"},
    limit=10,
)
```

### Neo4j (Knowledge Graph)

```python
from src.app.clients.neo4j import get_neo4j_client

neo4j = get_neo4j_client()
results = await neo4j.run_query(
    """
    MATCH (d:Document)-[:RELATED_TO]->(rd:Document)
    WHERE d.id = $doc_id
    RETURN rd
    """,
    {"doc_id": "doc-123"},
)
```

### Supabase

```python
from src.app.clients.supabase import get_supabase_client

supabase = get_supabase_client()
response = supabase.table("documents").select("*").execute()
```

## Testing

```bash
# Run all tests
just test

# Run with coverage
just test-cov

# Run specific test file
just test-file test/workflow/test_document_processing.py
```

## Development Tools

### Repository Policy Checker

Validates architectural conventions:

```bash
python tool/check_repo_policy.py
```

Checks:
- Directory structure (singular naming)
- Import dependencies
- Required files

### Prompt Loader

Load and validate prompts:

```python
from tool.prompt_loader import load_prompt, list_prompts

# List all prompts
prompts = list_prompts()

# Load specific prompt
template = load_prompt("api-calling/question-answering.v1.prompt.yaml")
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Temporal
TEMPORAL_ADDRESS=localhost:7233

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Weaviate
WEAVIATE_URL=http://localhost:8081

# LLM APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

## Next Steps

- See [EXTENSIONS_INDEX.md](EXTENSIONS_INDEX.md) for available extensions
- Add custom workflows with `prompt/coding/add-workflow.prompt.md`
- Deploy to GCP with `just deploy`
