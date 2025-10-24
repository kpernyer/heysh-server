# Workflow Builder Implementation Guide

This guide explains how to use the workflow builder system to let users specify actors (humans and AI agents) and workflows via a web interface that generates YAML for Temporal workflows.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ WorkflowBuilder│  │ ActorLibrary │  │ ActivityConfig  │ │
│  │   Component    │  │  Component   │  │   Component     │ │
│  └────────┬───────┘  └──────┬───────┘  └────────┬────────┘ │
│           │                  │                   │           │
│           └──────────────────┴───────────────────┘           │
│                              │                                │
│                    Generates YAML                             │
│                              ▼                                │
└──────────────────────────────────────────────────────────────┘
                               │
                               │ API Call
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Python)                          │
│  ┌──────────────────┐      ┌──────────────────────┐        │
│  │  YAML Parser     │──────│  Workflow Generator   │        │
│  │  & Validator     │      │  (Optional)           │        │
│  └────────┬─────────┘      └──────────┬────────────┘        │
│           │                           │                      │
│           ▼                           ▼                      │
│  ┌──────────────────┐      ┌──────────────────────┐        │
│  │ Temporal Worker  │      │  Temporal Activities │        │
│  │  (Registers      │◄─────│  (AI Agents, APIs,   │        │
│  │   Workflows)     │      │   External Services) │        │
│  └──────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Components Created

### Frontend (`src/`)

1. **Types** (`src/types/workflow.ts`)
   - TypeScript interfaces for workflow definitions
   - Type-safe actor and activity configurations

2. **Utilities** (`src/lib/workflow-utils.ts`)
   - YAML generation from workflow definition
   - YAML parsing to workflow definition
   - Validation logic

3. **UI Components** (`src/components/workflow/`)
   - `WorkflowBuilder.tsx` - Main orchestrator component
   - `ActorLibrary.tsx` - Actor management sidebar
   - `ActivityConfiguration.tsx` - Activity detail editor
   - `WorkflowCanvas.tsx` - Visual workflow editor

### Backend (`backend/`)

1. **Schemas** (`backend/src/app/schemas/workflow_schema.py`)
   - Pydantic models for YAML validation
   - Type-safe Python representations

2. **Parser** (`backend/src/app/utils/workflow_parser.py`)
   - YAML loading and validation
   - File I/O operations

3. **Activities** (`backend/activity/ai_agent_activities.py`)
   - Temporal activity implementations
   - AI agent execution logic
   - Generic activity executor

4. **Workflows** (`backend/workflow/generated_workflow.py`)
   - Example generated Temporal workflow
   - Shows how to map YAML to Temporal code

### Examples (`examples/workflows/`)

1. `document-review.workflow.yaml` - Complete document review workflow
2. `customer-onboarding.workflow.yaml` - Customer onboarding with human touchpoints

## Usage Guide

### 1. Define Actors in the UI

Actors are the entities that perform activities in your workflow:

**AI Agent Example:**
```typescript
{
  type: 'ai-agent',
  name: 'Document Summarizer',
  config: {
    model: 'claude-3-5-sonnet',
    capabilities: ['summarization', 'analysis'],
    systemPrompt: 'You are an expert document analyzer',
    temperature: 0.7
  }
}
```

**Human Example:**
```typescript
{
  type: 'human',
  name: 'Domain Administrator',
  config: {
    role: 'domain-admin',
    notificationChannels: ['email', 'in-app']
  }
}
```

### 2. Define Activities

Activities are the tasks performed by actors:

**AI Activity Example:**
```typescript
{
  actorId: 'ai-summarizer',
  activityType: 'temporal-activity',
  functionName: 'summarize_content',
  inputs: [
    { name: 'extracted_text', type: 'string', required: true }
  ],
  outputs: [
    { name: 'summary', type: 'string' }
  ],
  timeout: '3m',
  retryPolicy: { maxAttempts: 2 }
}
```

**Human Task Example:**
```typescript
{
  actorId: 'domain-admin',
  activityType: 'human-task',
  functionName: 'review_document',
  inputs: [
    { name: 'document_id', type: 'string', required: true },
    { name: 'summary', type: 'string', required: true }
  ],
  outputs: [
    { name: 'approved', type: 'boolean' }
  ],
  uiConfig: {
    formType: 'review-form',
    timeout: '7d',
    reminderAfter: '1d',
    fields: [
      { name: 'approved', label: 'Approve?', type: 'radio', options: ['Approve', 'Reject'] }
    ]
  }
}
```

### 3. Build Workflow Flow

Define the execution sequence:

```yaml
workflow_definition:
  start: "extract-content"
  steps:
    - step: "extract-content"
      on_success: "summarize"
      on_failure: "notify-error"

    - step: "summarize"
      conditions:
        - if: "quality_score >= 7"
          then: "publish"
        - if: "quality_score < 7"
          then: "human-review"
```

### 4. Generate YAML

Click "Generate YAML" to create the workflow definition:

```yaml
version: "1.0"
workflow:
  name: "document-review-workflow"
actors:
  - id: "ai-summarizer"
    type: "ai-agent"
    # ... actor config
activities:
  - id: "summarize"
    actor: "ai-summarizer"
    # ... activity config
workflow_definition:
  start: "extract-content"
  steps: [...]
```

### 5. Backend Processing

The backend receives the YAML and:

1. **Validates** the workflow definition
   ```python
   from app.utils.workflow_parser import parse_workflow_yaml

   workflow = parse_workflow_yaml(yaml_string)
   errors = workflow.validate_references()
   ```

2. **Registers** with Temporal worker
   ```python
   from workflow.generated_workflow import DocumentReviewWorkflow

   worker = Worker(
       client,
       task_queue="main-queue",
       workflows=[DocumentReviewWorkflow],
       activities=[extract_document_content, ...]
   )
   ```

3. **Executes** workflows
   ```python
   result = await client.execute_workflow(
       DocumentReviewWorkflow.run,
       args={"document_id": "doc-123", "user_id": "user-456"},
       id="review-doc-123",
       task_queue="main-queue"
   )
   ```

## Key Features

### Human-in-the-Loop Tasks

Human tasks pause the workflow and wait for human input:

```python
# In the workflow
await workflow.wait_condition(
    lambda: self.review_completed,
    timeout=timedelta(days=7)
)

# Signal to resume
@workflow.signal
async def submit_review(self, review_data: Dict[str, Any]):
    self.review_result = review_data
    self.review_completed = True
```

### AI Agent Execution

AI agents are executed as Temporal activities:

```python
@activity.defn(name="ai-agent.execute")
async def execute_ai_agent_activity(
    actor_config: Dict[str, Any],
    function_name: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    # Route to Claude, GPT, etc based on config
    if model.startswith("claude"):
        return await _execute_claude(...)
```

### Conditional Branching

Workflows support conditional logic:

```yaml
conditions:
  - if: "quality_score >= 7 && compliance_status == 'compliant'"
    then: "publish-document"
  - if: "quality_score < 4"
    then: "archive-document"
  - if: "quality_score >= 4 && quality_score < 7"
    then: "human-review"
```

## Integration Steps

### Frontend Integration

1. Add workflow builder to your app:
   ```tsx
   import { WorkflowBuilder } from '@/components/workflow/WorkflowBuilder';

   <WorkflowBuilder
     onSave={(workflow) => {
       // Save to backend
       const yaml = workflowToYAML(workflow);
       api.post('/workflows', { yaml });
     }}
   />
   ```

2. Install dependencies:
   ```bash
   npm install js-yaml
   npm install lucide-react  # Icons
   ```

### Backend Integration

1. Install dependencies:
   ```bash
   cd backend
   uv pip install pyyaml anthropic openai
   ```

2. Create API endpoint:
   ```python
   from fastapi import FastAPI, HTTPException
   from app.utils.workflow_parser import parse_workflow_yaml

   @app.post("/api/workflows")
   async def create_workflow(yaml_content: str):
       try:
           workflow = parse_workflow_yaml(yaml_content)
           # Save to database
           # Register with Temporal
           return {"success": True, "workflow_id": workflow.id}
       except Exception as e:
           raise HTTPException(400, str(e))
   ```

3. Start Temporal worker:
   ```bash
   just worker  # If using justfile
   ```

## Next Steps

1. **Enhance UI**: Add React Flow for visual graph editor
2. **Code Generation**: Auto-generate Python workflow code from YAML
3. **Testing**: Add workflow simulation/testing tools
4. **Monitoring**: Build workflow execution dashboard
5. **Templates**: Create workflow templates for common patterns

## Resources

- Example workflows: `examples/workflows/`
- Frontend types: `src/types/workflow.ts`
- Backend schemas: `backend/src/app/schemas/workflow_schema.py`
- Temporal docs: https://docs.temporal.io
