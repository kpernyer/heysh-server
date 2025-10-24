# Using Lovable with Backend

Lovable **cannot run** the Python backend, Docker, or database services. You have three options:

---

## Option 1: Local Backend + ngrok (Recommended for Development)

**Use when:** Actively developing both frontend and backend

### Setup

```bash
# Terminal 1: Start backend services
cd backend
just dev

# Terminal 2: Expose backend to internet
cd backend
just expose

# This will show you a public URL like:
# https://abc123.ngrok.io
```

### In Lovable

Create an environment variable:

```typescript
// src/config/api.ts
export const API_URL = import.meta.env.VITE_API_URL || 'https://abc123.ngrok.io';
```

In Lovable, set environment variable:
- `VITE_API_URL=https://abc123.ngrok.io` (copy from ngrok output)

Now Lovable can call your local backend!

**Pros:**
- ✅ Real backend with real data
- ✅ Fast iteration on both sides
- ✅ Lovable previews work

**Cons:**
- ❌ Need to keep backend running
- ❌ ngrok URL changes each restart (unless you pay)

---

## Option 2: Cloud Backend (Recommended for Sharing/Demos)

**Use when:** Showing work to others, or want stable API

### Setup

```bash
# Deploy backend once
cd backend
just deploy
```

This deploys to GCP Cloud Run and gives you: `https://api.hey.sh`

### In Lovable

```typescript
// src/config/api.ts
export const API_URL = 'https://api.hey.sh';
```

**Pros:**
- ✅ Stable URL
- ✅ No local backend needed
- ✅ Anyone can use Lovable previews

**Cons:**
- ❌ Slower to iterate (need to redeploy)
- ❌ Costs money (~$300/month)

---

## Option 3: Mock API (Quick Prototyping)

**Use when:** Building UX first, backend later

### In Lovable

```typescript
// src/lib/api.ts
const USE_MOCK = true; // Toggle this

export async function uploadDocument(file: File, domainId: string) {
  if (USE_MOCK) {
    // Mock response
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      workflow_id: `doc-${Date.now()}`,
      status: 'processing',
      message: 'Document processing started',
    };
  }

  // Real API call
  const response = await fetch(`${API_URL}/api/v1/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: crypto.randomUUID(),
      domain_id: domainId,
      file_path: file.name,
    }),
  });

  return response.json();
}
```

**Pros:**
- ✅ No backend needed
- ✅ Fast UX iteration
- ✅ Works immediately in Lovable

**Cons:**
- ❌ Not testing real integration
- ❌ Need to switch to real API later

---

## Recommended Workflow

### Phase 1: Prototype in Lovable (Mock API)
```typescript
const USE_MOCK = true;
```
- Build domain management UI
- Build document upload UI
- Build Q&A interface
- Get UX right first

### Phase 2: Connect to Local Backend (ngrok)
```bash
cd backend && just dev
cd backend && just expose  # Terminal 2
```
```typescript
const API_URL = 'https://abc123.ngrok.io';
const USE_MOCK = false;
```
- Test real API integration
- Debug backend issues
- Verify workflows work

### Phase 3: Deploy to Cloud
```bash
cd backend && just deploy
```
```typescript
const API_URL = 'https://api.hey.sh';
```
- Share with others
- Production-ready
- No local backend needed

---

## API Endpoints Available

Once backend is running (local or cloud):

### Documents
```typescript
POST /api/v1/documents
{
  "document_id": "doc-123",
  "domain_id": "my-domain",
  "file_path": "path/to/file.pdf"
}
```

### Questions
```typescript
POST /api/v1/questions
{
  "question_id": "q-456",
  "question": "What is the main topic?",
  "domain_id": "my-domain",
  "user_id": "user-789"
}
```

### Reviews
```typescript
POST /api/v1/reviews
{
  "review_id": "review-123",
  "reviewable_type": "answer",
  "reviewable_id": "q-456",
  "domain_id": "my-domain"
}
```

### Workflow Status
```typescript
GET /api/v1/workflows/{workflow_id}
```

---

## Example: Calling Backend from Lovable

```typescript
// src/lib/api/documents.ts
import { API_URL } from '@/config/api';

export async function uploadDocument(file: File, domainId: string) {
  // 1. Upload file to Supabase Storage (you already have this)
  const { data: storageData, error: storageError } = await supabase
    .storage
    .from('documents')
    .upload(`${domainId}/${file.name}`, file);

  if (storageError) throw storageError;

  // 2. Trigger backend workflow
  const response = await fetch(`${API_URL}/api/v1/documents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`, // If using auth
    },
    body: JSON.stringify({
      document_id: crypto.randomUUID(),
      domain_id: domainId,
      file_path: storageData.path,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to start document processing');
  }

  const result = await response.json();

  // 3. Poll for status or subscribe to updates
  return result.workflow_id;
}
```

---

## Testing Backend Connection

### From Lovable

Add a health check:

```typescript
// src/components/HealthCheck.tsx
import { useEffect, useState } from 'react';
import { API_URL } from '@/config/api';

export function HealthCheck() {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'error'>('checking');

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then(res => res.json())
      .then(() => setStatus('healthy'))
      .catch(() => setStatus('error'));
  }, []);

  return (
    <div>
      Backend: {status === 'healthy' ? '✅' : status === 'error' ? '❌' : '⏳'}
      <br />
      <small>{API_URL}</small>
    </div>
  );
}
```

---

## Summary

| Option | When to Use | Backend Runs Where |
|--------|-------------|-------------------|
| **Local + ngrok** | Active development | Your computer |
| **Cloud** | Sharing/demos | GCP Cloud Run |
| **Mock** | UX-first prototyping | Nowhere (mocked) |

**My recommendation:** Start with Mock in Lovable, then switch to Local+ngrok when you're ready to test real integration.

You **do not** need managed cloud services (Temporal Cloud, Neo4j Aura) until you deploy to production. Local Docker services work great for development!
