# Temporal Integration Guide

## Overview

The frontend now connects directly to Temporal to start workflows, query status, and send signals. This creates a clean separation:

- **Frontend** → Supabase (Auth, Postgres, Storage) + Temporal Client
- **Backend** → Temporal Workers (Execute workflows & activities)
- **No Direct Frontend Access** → Weaviate, Neo4j, AI APIs

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                 Frontend (TypeScript)                   │
│                                                         │
│  1. User uploads document → Supabase Storage           │
│  2. Create document record → Supabase Postgres         │
│  3. Start workflow → Temporal Server                   │
│  4. Poll workflow status → Temporal Server             │
│  5. Send signals (approve/reject) → Temporal Server    │
└────────────────────┬───────────────────────────────────┘
                     │
                     │ Temporal gRPC
                     ▼
┌────────────────────────────────────────────────────────┐
│              Temporal Server (localhost:7233)          │
│                                                         │
│  • Maintains workflow state                            │
│  • Routes activities to workers                        │
│  • Handles signals & queries                           │
│  • Persists history                                    │
└────────────────────┬───────────────────────────────────┘
                     │
                     │ Task Queue: main-queue
                     ▼
┌────────────────────────────────────────────────────────┐
│              Temporal Worker (Python)                  │
│                                                         │
│  Activities:                                           │
│  • extract_document_content                            │
│  • assess_document_quality (AI)                        │
│  • generate_embeddings → Weaviate                      │
│  • extract_knowledge_graph → Neo4j                     │
│  • publish_document                                    │
│  • notify_user                                         │
└────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies

Already installed:
```bash
pnpm install @temporalio/client @temporalio/common
```

### 2. Environment Configuration

Create `.env.local`:
```bash
# Temporal Connection
VITE_TEMPORAL_ADDRESS=localhost:7233
VITE_TEMPORAL_NAMESPACE=default

# Supabase (already configured)
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Start Temporal Server

**Option A: Temporal CLI (Recommended for local dev)**
```bash
temporal server start-dev
```

**Option B: Docker Compose**
```bash
cd backend
docker-compose up temporal
```

Temporal UI will be available at: http://localhost:8233

### 4. Start Backend Worker

```bash
cd backend
just worker
```

## Usage Examples

### 1. Document Upload Flow

```typescript
// In DocumentUpload component
import { startDocumentReviewWorkflow } from '@/lib/temporal-client';

// Upload to Supabase Storage
const { data: uploadData } = await supabase.storage
  .from('documents')
  .upload(`${domainId}/${fileName}`, file);

// Create document record
const { data: document } = await supabase
  .from('documents')
  .insert({
    name: fileName,
    file_path: uploadData.path,
    status: 'processing',
  })
  .select()
  .single();

// Start Temporal workflow
const workflowHandle = await startDocumentReviewWorkflow({
  documentId: document.id,
  userId: user.id,
  domainId: domainId,
  filePath: uploadData.path,
});

console.log(`Workflow started: ${workflowHandle.workflowId}`);
```

### 2. Monitor Workflow Status

```typescript
import { useWorkflowStatus } from '@/hooks/useTemporalWorkflow';

function DocumentStatus({ workflowId }) {
  const { status, loading } = useWorkflowStatus(workflowId, 5000); // Poll every 5s

  return (
    <WorkflowStatusCard
      workflowId={workflowId}
      title="Document Processing"
    />
  );
}
```

### 3. Human Review (Send Signal)

```typescript
import { DocumentReviewPanel } from '@/components/workflow/DocumentReviewPanel';

function ReviewPage({ workflowId, documentName }) {
  return (
    <DocumentReviewPanel
      workflowId={workflowId}
      documentName={documentName}
      aiRecommendation={{
        quality_score: 7.5,
        adds_knowledge: true,
        divergence_risk: false,
        recommendation: "Good quality document, recommend approval"
      }}
      onReviewSubmitted={() => {
        console.log('Review submitted');
      }}
    />
  );
}
```

## Components Created

### Core Utilities

1. **`src/lib/temporal-client.ts`** - Temporal client singleton
   - `getTemporalClient()` - Get/create client
   - `startWorkflow()` - Generic workflow starter
   - `signalWorkflow()` - Send signal to workflow
   - `queryWorkflow()` - Query workflow state
   - `startDocumentReviewWorkflow()` - Specific helper
   - `submitDocumentReview()` - Send review signal

2. **`src/hooks/useTemporalWorkflow.tsx`** - React hooks
   - `useWorkflow()` - Manage workflow lifecycle
   - `useWorkflowStatus()` - Poll workflow status
   - `useDocumentReviewWorkflow()` - Document-specific hook

### UI Components

1. **`WorkflowStatusBadge`** - Status indicator (Running, Completed, Failed)
2. **`WorkflowStatusCard`** - Full workflow status display with polling
3. **`DocumentReviewPanel`** - Human review form with AI recommendations

## Backend Workflow (Python)

The backend workflow receives these signals:

```python
@workflow.defn
class DocumentReviewWorkflow:
    def __init__(self):
        self.review_completed = False
        self.review_result = None

    @workflow.run
    async def run(self, documentId: str, userId: str, domainId: str):
        # 1. Extract content
        content = await workflow.execute_activity(
            extract_document_content,
            args=[documentId],
        )

        # 2. AI quality check
        quality = await workflow.execute_activity(
            assess_document_quality,
            args=[content],
        )

        # 3. Wait for human review if needed
        if quality['score'] < 7:
            await workflow.wait_condition(
                lambda: self.review_completed,
                timeout=timedelta(days=7)
            )

            if self.review_result['approved']:
                # Publish
                await workflow.execute_activity(publish_document, ...)
            else:
                # Archive
                await workflow.execute_activity(archive_document, ...)

    @workflow.signal
    async def submit_review(self, review_data: dict):
        """Frontend sends signal here"""
        self.review_result = review_data
        self.review_completed = True

    @workflow.query
    def get_status(self) -> dict:
        """Frontend queries status here"""
        return {
            'review_completed': self.review_completed,
            'review_result': self.review_result,
        }
```

## Data Flow Example

### Document Upload → Review → Publish

1. **User uploads document**
   - Frontend uploads to Supabase Storage
   - Creates document record (status: `processing`)
   - Starts `document-review-workflow`

2. **Workflow executes**
   - Activity: Extract content from file
   - Activity: Generate embeddings → Weaviate
   - Activity: AI quality assessment
   - Activity: Extract entities → Neo4j

3. **AI decision point**
   - High quality (score ≥ 8) → Auto-publish
   - Low quality (score < 4) → Auto-reject
   - Medium quality → Wait for human review

4. **Human review** (if needed)
   - Workflow pauses with `wait_condition`
   - Frontend shows `DocumentReviewPanel`
   - User approves/rejects → Sends signal
   - Workflow resumes

5. **Finalization**
   - Activity: Publish to knowledge base (or archive)
   - Activity: Update document status
   - Activity: Notify contributor
   - Workflow completes

## Benefits

### ✅ Clean Separation
- Frontend doesn't need to know about Weaviate, Neo4j
- All complex logic in backend workflows
- Easy to test and modify

### ✅ Reliability
- Temporal handles retries automatically
- Workflow state persists across crashes
- Can pause for hours/days waiting for human input

### ✅ Visibility
- Temporal UI shows all workflows
- Can see exactly where each document is in the process
- Easy debugging

### ✅ Scalability
- Workers can be scaled independently
- Frontend doesn't wait for long-running operations
- Async by default

## Troubleshooting

### Connection Refused
```
Error: Failed to connect to Temporal server
```
**Solution:** Make sure Temporal server is running:
```bash
temporal server start-dev
```

### Workflow Not Starting
Check:
1. Backend worker is running: `just worker`
2. Workflow is registered in worker
3. Task queue name matches: `main-queue`

### Signal Not Received
Check:
1. Workflow ID is correct
2. Signal name matches: `submit_review`
3. Workflow hasn't completed yet

### Status Not Updating
Check:
1. Polling is enabled (default 5s)
2. Workflow ID hasn't changed
3. Network connection to Temporal server

## Next Steps

1. **Add Inbox Integration** - Show pending reviews in user inbox
2. **Add Notifications** - Realtime updates via Supabase Realtime
3. **Add Workflow Templates** - Pre-configured workflows for common patterns
4. **Add Metrics** - Track workflow performance
5. **Add Error Handling** - Graceful degradation when Temporal unavailable

## Security Notes

- Temporal connection is **not authenticated** in dev mode
- For production: Use Temporal Cloud with mTLS
- Never expose Temporal credentials in frontend
- Use Supabase RLS to control who can start workflows
