# ✅ Hey.sh Backend Setup Complete

The full backend directory structure has been created following Kenneth Pernyer's singular directory conventions.

## 📁 Directory Structure

```
backend/
├── workflow/              # Temporal workflow definitions (3 workflows)
│   ├── document_processing.py
│   ├── question_answering.py
│   └── quality_review.py
│
├── activity/              # Temporal activities (5 modules)
│   ├── document.py        # Document processing
│   ├── search.py          # Vector & graph search
│   ├── llm.py            # LLM generation
│   └── supabase.py       # Database operations
│
├── worker/               # Temporal workers
│   └── main.py           # Worker process
│
├── service/              # FastAPI services
│   └── api.py            # REST API endpoints
│
├── src/app/              # Shared application code
│   ├── clients/          # Database/API clients
│   │   ├── supabase.py
│   │   ├── weaviate.py
│   │   ├── neo4j.py
│   │   └── llm.py
│   ├── models/           # Data models
│   ├── schemas/          # Pydantic schemas
│   │   ├── requests.py
│   │   └── responses.py
│   └── utils/            # Utilities
│       ├── text_extraction.py
│       ├── embeddings.py
│       └── prompts.py
│
├── prompt/               # Prompts-as-code
│   ├── coding/           # Code generation prompts
│   │   ├── add-workflow.prompt.md
│   │   └── add-activity.prompt.md
│   └── api-calling/      # LLM API prompts
│       ├── question-answering.v1.prompt.yaml
│       └── summarize-document.v1.prompt.yaml
│
├── tool/                 # Development tools
│   ├── check_repo_policy.py
│   └── prompt_loader.py
│
├── script/               # Executable scripts
│   └── render_prompt.py
│
├── test/                 # Tests
│   ├── workflow/
│   ├── activity/
│   ├── service/
│   └── structure/
│       ├── test_prompts_compile.py
│       └── test_repo_structure.py
│
├── infra/                # Infrastructure as code
│   ├── terraform/        # GCP deployment
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   └── k8s/             # Kubernetes manifests
│       ├── temporal.yaml
│       └── neo4j.yaml
│
├── docker/               # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── docs/                 # Documentation
│   ├── basics.md         # Getting started guide
│   └── EXTENSIONS_INDEX.md
│
├── pyproject.toml        # Python dependencies
├── justfile              # Command runner
├── .gitignore
├── .pre-commit-config.yaml
├── .env.example
├── README.md
└── bootstrap.sh          # Setup script
```

## 🚀 Quick Start

### 1. Bootstrap

```bash
cd backend
./bootstrap.sh
```

This installs:
- `uv` (Python package manager)
- `just` (command runner)
- Checks prerequisites

### 2. Install Dependencies

```bash
just bootstrap
```

### 3. Configure Environment

Edit `.env` with your credentials:
```bash
cp .env.example .env
# Edit .env with your Supabase, Neo4j, Weaviate, API keys
```

### 4. Start Development Environment

```bash
just dev
```

This starts:
- **Temporal UI**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **Weaviate**: http://localhost:8081
- **FastAPI**: http://localhost:8000

## 🔧 Available Commands

```bash
just bootstrap       # Setup development environment
just dev            # Start all services
just dev-stop       # Stop all services
just test           # Run test suite
just test-cov       # Run tests with coverage
just lint           # Lint code
just fmt            # Format code
just check-structure # Validate repo structure
just worker         # Run Temporal worker
just deploy         # Deploy to GCP
```

## 📊 Architecture Components

### Temporal Workflows

1. **DocumentProcessingWorkflow** - Process uploaded documents
   - Download from Supabase
   - Extract text
   - Generate embeddings
   - Index in Weaviate
   - Update Neo4j graph

2. **QuestionAnsweringWorkflow** - Answer user questions
   - Vector search (Weaviate)
   - Graph traversal (Neo4j)
   - LLM generation
   - Confidence scoring
   - Human review trigger

3. **QualityReviewWorkflow** - Human-in-the-loop review
   - Assign to reviewers
   - Apply decisions
   - Update quality scores
   - Notify contributors

### Database Integrations

- **Supabase**: User data, documents, questions
- **Weaviate**: Vector search for semantic queries
- **Neo4j**: Knowledge graph for relationships
- **PostgreSQL**: Temporal server backend

### API Endpoints

```
POST /api/v1/documents     - Upload document
POST /api/v1/questions     - Ask question
POST /api/v1/reviews       - Submit review
GET  /api/v1/workflows/:id - Get workflow status
```

## 📝 Prompts-as-Code System

### API-Calling Prompts (YAML)

```yaml
# prompt/api-calling/question-answering.v1.prompt.yaml
version: 1
model: claude-3-5-sonnet-20250219
temperature: 0.3
user_template: |
  Question: {{ question }}
  Context: {{ context }}
```

Render with:
```bash
just render-prompt prompt/api-calling/question-answering.v1.prompt.yaml \
  '{"question":"...","context":[]}'
```

### Coding Prompts (Markdown)

```markdown
# prompt/coding/add-workflow.prompt.md
---
id: add-temporal-workflow
version: 1
audience: "Claude|Cursor"
---
Template for creating new workflows...
```

Use with Claude Code or Cursor AI.

## 🏗️ Import Dependency Rules

**Critical architectural constraint** (enforced by `tool/check_repo_policy.py`):

✅ **Allowed:**
- `workflow/` → `activity/`, `src/app/`
- `activity/` → `src/app/`
- `worker/` → `workflow/`, `activity/`, `src/app/`
- `service/` → `src/app/`, `workflow/`

❌ **Forbidden:**
- `src/app/` → `workflow/`, `activity/`, `worker/`, `service/`

This ensures core app logic stays independent of orchestration.

## 🧪 Testing

```bash
# Run all tests
just test

# Structure tests validate:
pytest test/structure/
```

Tests include:
- Repository structure validation
- Prompt compilation checks
- Import dependency rules
- Workflow tests (placeholder)
- Activity tests (placeholder)

## 🚢 Deployment to Google Cloud

### Terraform Setup

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project ID

terraform init
terraform plan
terraform apply
```

This creates:
- GKE cluster for Temporal, Neo4j, Weaviate
- Cloud Run service for backend API
- Secret Manager for credentials
- Service accounts with proper permissions

### Docker Build & Deploy

```bash
just docker-build
just deploy
```

## 📚 Documentation

- **[backend/docs/basics.md](backend/docs/basics.md)** - Complete getting started guide
- **[backend/docs/EXTENSIONS_INDEX.md](backend/docs/EXTENSIONS_INDEX.md)** - 10 planned extensions:
  1. Advanced Workflows
  2. Vector Search Optimization
  3. Knowledge Graph Advanced Queries
  4. Authentication & Authorization
  5. Monitoring & Observability
  6. Database Migrations
  7. Background Jobs & Scheduling
  8. Advanced Testing Strategies
  9. Multi-Tenancy
  10. Production Deployment

## 🔐 Environment Variables

Required in `.env`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

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

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
```

## 🎯 Next Steps

1. **Configure environment** - Edit `.env` with your credentials
2. **Start services** - Run `just dev`
3. **Test API** - Try example requests to http://localhost:8000
4. **Explore Temporal UI** - Visit http://localhost:8080
5. **Add workflows** - Use prompts in `prompt/coding/`
6. **Deploy** - Follow Terraform guide for GCP deployment

## 🔗 Integration with Frontend

Your React frontend can call the backend API:

```typescript
// frontend/src/integrations/backend/client.ts
const BACKEND_API = 'http://localhost:8000';

export async function uploadDocument(file: File, domainId: string) {
  // 1. Upload to Supabase Storage
  const { data } = await supabase.storage
    .from('documents')
    .upload(`${domainId}/${file.name}`, file);

  // 2. Trigger backend workflow
  const response = await fetch(`${BACKEND_API}/api/v1/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: data.id,
      domain_id: domainId,
      file_path: data.path
    })
  });

  return response.json();
}
```

## ✨ Key Features Implemented

- ✅ Singular directory structure
- ✅ Temporal workflows (3 core workflows)
- ✅ Temporal activities (modular, reusable)
- ✅ FastAPI REST API
- ✅ Weaviate vector search integration
- ✅ Neo4j knowledge graph integration
- ✅ Supabase database client
- ✅ LLM client (Anthropic Claude)
- ✅ Prompts-as-code system
- ✅ Repository policy enforcement
- ✅ Structured testing framework
- ✅ Docker Compose for local dev
- ✅ Terraform for GCP deployment
- ✅ Comprehensive documentation
- ✅ Bootstrap automation script

## 📞 Support

For questions or issues:
- Check [docs/basics.md](backend/docs/basics.md)
- Run `just check-structure` to validate setup
- Review logs in Docker containers

---

**🎉 Backend setup is complete and ready for development!**

Run `cd backend && ./bootstrap.sh` to get started.
