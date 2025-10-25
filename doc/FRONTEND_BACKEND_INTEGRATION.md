# Frontend ↔ Backend Integration

## ❌ WRONG: Using Temporal Client in Frontend

**DON'T DO THIS:**
```typescript
// ❌ This won't work - @temporalio/client is for Node.js only!
import { Client } from '@temporalio/client';

const client = await Client.connect({ address: 'localhost:7233' });
await client.workflow.start('MyWorkflow', { args: [...] });
```

**Problem:** `@temporalio/client` is a Node.js library and cannot run in browsers.

---

## ✅ CORRECT: Call FastAPI Backend

**Frontend calls FastAPI, FastAPI calls Temporal:**

```
Frontend (Browser)
    ↓ HTTP REST
FastAPI Backend (service/api.py)
    ↓ Temporal Client
Temporal Server
```

### Use the Backend API Client

```typescript
// ✅ Correct - Call the FastAPI backend
import { uploadDocument, askQuestion, getWorkflowStatus } from '@/lib/backend-api';

// Upload a document
const result = await uploadDocument(
  'doc-123',
  'my-domain',
  'documents/file.pdf'
);

// Track the workflow
const status = await getWorkflowStatus(result.workflow_id);
```

---

## Example: Document Upload Flow

### 1. Upload File to Supabase Storage

```typescript
// Upload to Supabase Storage first
const { data, error } = await supabase
  .storage
  .from('documents')
  .upload(`${domainId}/${file.name}`, file);

if (error) throw error;
```

### 2. Trigger Backend Workflow

```typescript
// Trigger backend processing workflow
import { uploadDocument } from '@/lib/backend-api';

const workflow = await uploadDocument(
  crypto.randomUUID(),       // document_id
  domainId,                  // domain_id
  data.path                  // file_path in Supabase
);

console.log('Workflow started:', workflow.workflow_id);
```

### 3. Poll for Status (Optional)

```typescript
import { getWorkflowStatus } from '@/lib/backend-api';

const status = await getWorkflowStatus(workflow.workflow_id);
console.log('Status:', status.status); // "RUNNING", "COMPLETED", etc.
```

---

## Full Example: Upload Document Component

```typescript
import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { uploadDocument } from '@/lib/backend-api';

export function DocumentUpload({ domainId }: { domainId: string }) {
  const [uploading, setUploading] = useState(false);
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);

    try {
      // 1. Upload to Supabase Storage
      const { data, error } = await supabase
        .storage
        .from('documents')
        .upload(`${domainId}/${file.name}`, file);

      if (error) throw error;

      // 2. Trigger backend workflow
      const result = await uploadDocument(
        crypto.randomUUID(),
        domainId,
        data.path
      );

      setWorkflowId(result.workflow_id);
      console.log('Processing started:', result.workflow_id);

    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
        disabled={uploading}
      />
      {uploading && <p>Uploading...</p>}
      {workflowId && <p>Processing: {workflowId}</p>}
    </div>
  );
}
```

---

## Example: Ask Question Component

```typescript
import { useState } from 'react';
import { askQuestion } from '@/lib/backend-api';

export function AskQuestion({ domainId, userId }: Props) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);

    try {
      const result = await askQuestion(
        crypto.randomUUID(),
        question,
        domainId,
        userId
      );

      console.log('Answer workflow started:', result.workflow_id);
      // Poll for answer or subscribe to updates

    } catch (error) {
      console.error('Question failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question..."
      />
      <button onClick={handleSubmit} disabled={loading}>
        Ask
      </button>
    </div>
  );
}
```

---

## Environment Variables

Create `.env.local`:

```bash
# Local development
VITE_API_URL=http://localhost:8001

# With ngrok (for Lovable)
# VITE_API_URL=https://abc123.ngrok.io

# Production
# VITE_API_URL=https://api.hey.sh
```

---

## API Endpoints

Your FastAPI backend exposes these endpoints:

```
POST   /api/v1/documents        # Upload document
POST   /api/v1/questions         # Ask question
POST   /api/v1/reviews           # Submit review
GET    /api/v1/workflows/{id}    # Get workflow status
GET    /health                   # Health check
```

All are wrapped in `src/lib/backend-api.ts`.

---

## Alternative: Supabase Edge Functions

If you don't want to run the backend locally, you could create Supabase Edge Functions that call Temporal. But this is more complex:

```typescript
// supabase/functions/trigger-workflow/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

serve(async (req) => {
  // Call your FastAPI backend or Temporal Cloud directly
  const response = await fetch('https://api.hey.sh/api/v1/documents', {
    method: 'POST',
    body: await req.text(),
  });

  return new Response(await response.text());
});
```

**But this is overkill!** Just call FastAPI directly from the frontend.

---

## Summary

❌ **Don't:** Use `@temporalio/client` in frontend
✅ **Do:** Call FastAPI backend via `src/lib/backend-api.ts`

The FastAPI backend handles all Temporal operations for you.
