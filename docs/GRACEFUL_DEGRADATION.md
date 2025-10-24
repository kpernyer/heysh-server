# Graceful Degradation: Temporal Unavailable

## Overview

The system now handles Temporal server unavailability gracefully, ensuring the application remains functional even when workflow automation is offline.

## What Happens When Temporal is Down?

### ✅ Application Still Works

**Documents can still be uploaded:**
- Files upload to Supabase Storage ✓
- Records created in Postgres ✓
- Status marked as `pending` instead of `processing`
- User sees informative message

**Manual workflows available:**
- Controllers can manually review documents
- Documents can be approved/rejected through UI
- No data loss occurs

### 🔄 Automatic Recovery

**Retry Logic:**
- 3 connection attempts with exponential backoff
- 1s → 2s → 3s delays between retries
- After retries exhausted, system enters fallback mode

**Connection Status Tracking:**
```typescript
{
  isAvailable: false,
  attempts: 3,
  lastError: Error('ECONNREFUSED'),
  hasClient: false
}
```

## User Experience

### When Temporal is Unavailable

**Document Upload:**
```
✓ Document Uploaded
Document uploaded successfully. Automated processing is
temporarily unavailable, but you can still review it manually.
```

**Status Indicator:**
```
⚠ Workflow automation temporarily unavailable  [Retry]
```

### When Temporal Reconnects

**Status Indicator:**
```
✓ Workflow automation active
```

**Future uploads** automatically use workflows again.

## Implementation Details

### 1. Connection Management

**File:** `src/lib/temporal-client.ts`

```typescript
// Singleton with state tracking
let isConnectionAvailable = true;
let connectionAttempts = 0;
let lastConnectionError: Error | null = null;

// Retry logic with exponential backoff
for (let attempt = 1; attempt <= maxRetries; attempt++) {
  try {
    connection = await Connection.connect({ address });
    // Success - reset state
    isConnectionAvailable = true;
    return client;
  } catch (error) {
    if (attempt < maxRetries) {
      await sleep(retryDelay * attempt); // 1s, 2s, 3s
    }
  }
}

// All retries failed
isConnectionAvailable = false;
throw new TemporalConnectionError('Connection failed');
```

### 2. Custom Error Type

```typescript
export class TemporalConnectionError extends Error {
  public readonly isTemporalError = true;

  constructor(message: string, public readonly originalError?: Error) {
    super(message);
    this.name = 'TemporalConnectionError';
  }
}

// Check if error is Temporal-related
export function isTemporalConnectionError(error: any): boolean {
  return error?.isTemporalError === true;
}
```

### 3. Graceful Fallback in Upload

**File:** `src/components/domain/DocumentUpload.tsx`

```typescript
try {
  // Try to start workflow
  await startDocumentReviewWorkflow({ documentId, ... });

  toast({
    title: "Success",
    description: "Document uploaded and processing started"
  });

} catch (workflowError) {
  const isTemporalDown = workflowError?.isTemporalError === true;

  if (isTemporalDown) {
    // Temporal unavailable - fallback mode
    await supabase
      .from('documents')
      .update({ status: 'pending' })
      .eq('id', documentId);

    toast({
      title: "Document Uploaded",
      description: "Automated processing temporarily unavailable, manual review available"
    });
  } else {
    // Other error - actual failure
    await supabase
      .from('documents')
      .update({ status: 'failed' })
      .eq('id', documentId);

    toast({
      title: "Processing failed",
      variant: "destructive"
    });
  }
}
```

### 4. Status Indicator Component

**File:** `src/components/workflow/TemporalStatusIndicator.tsx`

**Three Variants:**

1. **Badge** - Minimal indicator
```tsx
<TemporalStatusIndicator variant="badge" />
// Shows: "✓ Workflow Engine Online" or "⚠ Offline"
```

2. **Compact** - Inline message with retry
```tsx
<TemporalStatusIndicator variant="compact" checkOnMount />
// Shows: "⚠ Workflow automation temporarily unavailable [Retry]"
```

3. **Full** - Detailed alert with error info
```tsx
<TemporalStatusIndicator variant="full" showWhenConnected />
// Shows full error details and retry button
```

## Status Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│              User Uploads Document                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Upload to Supabase    │
        │  Create DB Record      │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Try Start Workflow    │
        └────┬──────────┬────────┘
             │          │
        Success      Failure
             │          │
             ▼          ▼
    ┌─────────────┐  ┌──────────────────────┐
    │  Processing │  │  Check Error Type    │
    │  (Workflow) │  └─────┬────────────────┘
    └─────────────┘        │
                           ▼
                  ┌────────────────┐
                  │ Temporal Error?│
                  └───┬────────┬───┘
                   Yes│        │No
                      │        │
                      ▼        ▼
              ┌──────────┐  ┌─────────┐
              │ Pending  │  │ Failed  │
              │ (Manual) │  │ (Error) │
              └──────────┘  └─────────┘
```

## Recovery Process

### Automatic Reconnection

**On next upload after Temporal comes back:**
1. User uploads document
2. System attempts Temporal connection (with retry)
3. If successful: `isConnectionAvailable = true`
4. Workflow starts normally
5. Status indicator updates automatically

**Manual Retry:**
```tsx
<Button onClick={handleRetry}>
  <RefreshCw /> Retry
</Button>

// Calls:
resetTemporalConnection();  // Clear error state
await checkTemporalConnection();  // Try reconnect
```

### Pending Documents

Documents uploaded while Temporal was down (status: `pending`) can be:

1. **Manually reviewed** by controllers through UI
2. **Batch processed** when Temporal comes back (future feature)
3. **Re-triggered** individually (future feature)

## Configuration

**Environment Variables:**
```bash
VITE_TEMPORAL_ADDRESS=localhost:7233
VITE_TEMPORAL_NAMESPACE=default
```

**Retry Settings** (in code):
```typescript
const config = {
  maxRetries: 3,
  retryDelay: 1000,  // milliseconds
};
```

## Testing

### Simulate Temporal Down

1. **Stop Temporal server:**
```bash
# If using temporal CLI
pkill temporal

# If using docker
docker-compose stop temporal
```

2. **Upload document** - Should see graceful fallback

3. **Check status indicator** - Should show warning

### Simulate Recovery

1. **Start Temporal server:**
```bash
temporal server start-dev
```

2. **Click retry button** - Should reconnect

3. **Upload document** - Should start workflow normally

## Monitoring

### Check Connection Status

```typescript
import { getTemporalConnectionStatus } from '@/lib/temporal-client';

const status = getTemporalConnectionStatus();
console.log(status);
// {
//   isAvailable: false,
//   attempts: 3,
//   lastError: Error(...),
//   hasClient: false
// }
```

### Logs to Watch

```
[Temporal] Connected to localhost:7233 (namespace: default)
✓ Success

[Temporal] Connection attempt 1/3 failed: ECONNREFUSED
[Temporal] Connection attempt 2/3 failed: ECONNREFUSED
[Temporal] Connection attempt 3/3 failed: ECONNREFUSED
[Temporal] All connection attempts failed
✗ Failure

[Workflow] Started document review workflow: doc-review-123
✓ Workflow started

[Workflow] Failed to start workflow: TemporalConnectionError
✗ Workflow failed (graceful)
```

## Benefits

✅ **No data loss** - Documents always uploaded
✅ **User informed** - Clear status messages
✅ **Manual fallback** - System remains usable
✅ **Automatic recovery** - Reconnects when possible
✅ **No crashes** - Errors handled gracefully
✅ **Debugging friendly** - Clear error messages and state

## Production Recommendations

1. **Use Temporal Cloud** - Higher availability
2. **Add monitoring** - Alert when Temporal is down
3. **Batch retry** - Process pending documents when recovered
4. **Health checks** - Regular connection checks
5. **Circuit breaker** - Prevent retry storms

## Future Enhancements

- [ ] Batch process `pending` documents when Temporal recovers
- [ ] Configurable retry strategy per environment
- [ ] Metrics dashboard for Temporal availability
- [ ] Queue pending workflows in Postgres
- [ ] Webhook notifications when Temporal status changes
