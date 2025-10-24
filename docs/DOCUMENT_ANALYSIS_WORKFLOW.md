# Document Analysis Workflow with HITL Controller Review

## 🎯 **Översikt**

Detta dokument beskriver den fullständiga Document Analysis Workflow som implementerar din vision:

1. **Dokumentuppladdning** → Supabase Storage (eller MinIO för dev)
2. **FörAnalys** → LLM-analys (senare Ollama)
3. **Beslutslogik** → Auto-approve, Controller review, eller reject
4. **HITL Review** → Controller inbox med Search Attributes
5. **Publicering** → Weaviate + Neo4j indexering

## 🏗️ **Arkitektur**

### **Workflow Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Analysis Workflow                │
├─────────────────────────────────────────────────────────────┤
│  1. Download Document (Supabase Storage)                    │
│  2. Extract Text & Metadata                                │
│  3. FörAnalys - AI Relevance Assessment                     │
│  4. Decision Logic:                                         │
│     • High Score (≥8.0) → Auto-approve → Publish            │
│     • Medium Score (7.0-8.0) → Controller Review           │
│     • Low Score (<7.0) → Reject                            │
│  5. Controller Inbox (Search Attributes)                   │
│  6. HITL Decision → Publish or Archive                     │
└─────────────────────────────────────────────────────────────┘
```

### **Multi-Queue Architecture**

- **`general-queue`** → Workflows
- **`ai-processing-queue`** → AI activities (text extraction, embeddings, LLM analysis)
- **`storage-queue`** → Storage activities (download, Weaviate, Neo4j, Supabase)

## 🚀 **API Endpoints**

### **Start Document Analysis**
```bash
POST /api/v1/analysis/documents
{
  "document_id": "doc-123",
  "domain_id": "domain-456",
  "file_path": "documents/doc-123/document.pdf",
  "contributor_id": "contributor-789",
  "domain_criteria": {
    "topics": ["technology", "AI"],
    "min_length": 1000,
    "quality_threshold": 8.0
  },
  "auto_approve_threshold": 8.0,
  "relevance_threshold": 7.0
}
```

### **Check Workflow Status**
```bash
GET /api/v1/analysis/workflows/{workflow_id}/status
```

### **Submit Controller Decision**
```bash
POST /api/v1/analysis/workflows/{workflow_id}/controller-decision
{
  "decision": "approve",  // or "reject"
  "controller_id": "controller-123",
  "feedback": "Good content, approved"
}
```

### **Query Controller Inbox**
```bash
GET /api/v1/analysis/controller/inbox?controller_id=controller-123
```

## 🔍 **Search Attributes för Controller Inbox**

Temporal använder Search Attributes för att skapa "inboxes":

```python
await workflow.upsert_search_attributes({
    "Assignee": "controller",           # All controllers can see this
    "Queue": "document-review",         # Queue type
    "Status": "pending",                # Current status
    "Priority": "normal",               # Priority level
    "DueAt": "2024-01-15T10:00:00Z",   # Deadline
    "Tenant": "domain-456",             # Domain/tenant
    "DocumentId": "doc-123",            # Document reference
    "ContributorId": "contributor-789", # Who submitted
    "RelevanceScore": 7.5,              # AI analysis score
})
```

**Controller Inbox Query:**
```python
workflows = await client.list_workflows(
    query='Assignee = "controller" AND Status = "pending" AND Queue = "document-review"'
)
```

## 🧪 **Test Scripts**

### **1. Direct Workflow Test**
```bash
just test-document-analysis
```
- Testar workflow direkt med Temporal Client
- Simulerar olika dokumentkvaliteter
- Demonstrerar HITL decision flow

### **2. API Endpoint Test**
```bash
just test-document-analysis-api
```
- Testar REST API endpoints
- Simulerar Controller decisions
- Testar inbox functionality

### **3. Full Demo**
```bash
just demo-document-analysis
```
- Startar Temporal Server
- Startar Workers
- Startar API Server
- Kör fullständig test suite

## 📊 **Workflow States**

### **Document Status**
- `UPLOADED` → Document uploaded to storage
- `ANALYZING` → AI analysis in progress
- `PENDING_REVIEW` → Waiting for Controller decision
- `APPROVED` → Controller approved
- `REJECTED` → Controller rejected or auto-rejected
- `PUBLISHED` → Indexed in Weaviate + Neo4j
- `ARCHIVED` → Rejected and archived

### **Decision Logic**
```python
if relevance_score >= auto_approve_threshold:
    # Auto-approve: High quality
    return await self._publish_document(...)
elif relevance_score >= relevance_threshold:
    # Send to Controller inbox
    return await self._send_to_controller_inbox(...)
else:
    # Reject: Too low quality
    return await self._reject_document(...)
```

## 🔄 **HITL (Human-in-the-Loop) Pattern**

### **1. Workflow waits for Controller decision**
```python
await workflow.wait_condition(
    lambda: self.controller_decision is not None,
    timeout=timedelta(days=7)  # 7-day deadline
)
```

### **2. Controller submits decision via signal**
```python
@workflow.signal
async def controller_decision(self, decision: str, controller_id: str, feedback: str = ""):
    self.controller_decision = decision
    self.controller_id = controller_id
    self.analysis_completed = True
```

### **3. Workflow applies decision**
```python
if self.controller_decision == "approve":
    return await self._publish_document(...)
else:
    return await self._reject_document(...)
```

## 🎯 **Nästa Steg**

### **1. Ollama Integration**
Ersätt LLM-anrop med lokal Ollama modell:
```python
# Nu: OpenAI GPT-4
model = "gpt-4o"

# Senare: Ollama
model = "llama3:8b"  # Lokal modell
```

### **2. MinIO för Development**
Konfigurera MinIO istället för Supabase Storage för lokal utveckling:
```python
# Development: MinIO
storage_url = "http://localhost:9000"
bucket = "documents"

# Production: Supabase
storage_url = "https://supabase.co"
bucket = "documents"
```

### **3. Advanced Search Attributes**
Utöka Search Attributes för mer avancerad inbox-funktionalitet:
```python
"Assignee": "controller-123",        # Specific controller
"Priority": "high",                 # Priority levels
"Category": "technical",             # Document categories
"Language": "en",                   # Document language
"DueAt": "2024-01-15T10:00:00Z",    # Deadlines
"Escalated": False,                  # Escalation status
```

### **4. Notification System**
Lägg till notifieringar för Controllers:
```python
# Slack notification
await workflow.execute_activity(
    notify_controller_activity,
    args=[controller_id, "New document needs review", document_id]
)

# Email notification
await workflow.execute_activity(
    send_email_activity,
    args=[controller_email, "Document Review Required", email_content]
)
```

## 🚀 **Kör Workflow**

### **Starta allt:**
```bash
# Terminal 1: Temporal Server
just start-temporal

# Terminal 2: Workers
just start-workers

# Terminal 3: API Server
just start-api

# Terminal 4: Test
just test-document-analysis
```

### **Eller kör full demo:**
```bash
just demo-document-analysis
```

## 📚 **Relaterade Filer**

- `workflow/document_analysis_workflow.py` - Huvudworkflow
- `service/routes_document_analysis.py` - API endpoints
- `test_document_analysis_workflow.py` - Workflow test
- `test_document_analysis_api.py` - API test
- `activity/ai.py` - AI analysis activities
- `activity/document.py` - Document processing activities
- `activity/search.py` - Weaviate/Neo4j activities

Detta implementerar exakt den vision du beskrev med Temporal workflows, HITL Controller review, och Search Attributes för inbox-funktionalitet! 🎉
