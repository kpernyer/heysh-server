# WebSocket Integration for Real-Time Temporal Workflow Signals

This document describes the complete WebSocket infrastructure implemented for real-time communication between Temporal workflows and the frontend.

## Overview

The WebSocket integration provides:
- **Real-time signals** from Temporal workflows to frontend clients
- **User-specific routing** of signals based on JWT authentication
- **Signal persistence** in database for inbox system
- **Auto-reconnection** with exponential backoff on frontend
- **Type-safe** signal handling with TypeScript interfaces

## Architecture

```
Frontend (React/Vite)
    ↓ WebSocket Connection (wss://api.hey.sh/ws)
    ↓ JWT Authentication
Backend (FastAPI)
    ↓ WebSocket Manager
    ↓ Signal Service
    ↓ Database Persistence
Temporal Workflows
    ↓ Signal Activities
    ↓ WebSocket Delivery
```

## Components

### 1. WebSocket Server (`service/websocket_routes.py`)

**Endpoint**: `wss://api.hey.sh/ws`

**Authentication**: JWT token via query parameter
```javascript
const ws = new WebSocket('wss://api.hey.sh/ws?token=your-jwt-token');
```

**Features**:
- JWT token validation
- User-specific connection management
- Ping/pong heartbeat support
- Automatic connection cleanup

### 2. Connection Manager (`service/websocket_manager.py`)

Manages WebSocket connections with:
- User-to-connections mapping
- Connection lifecycle management
- Signal routing to specific users
- Broadcast capabilities
- Connection health monitoring

### 3. Signal Service (`service/signal_service.py`)

Core service for sending signals:
- **Status Updates**: Workflow state changes
- **Progress Updates**: Step-by-step progress
- **Completion Signals**: Workflow results
- **Error Signals**: Error notifications

### 4. Enhanced Signal Service (`service/enhanced_signal_service.py`)

Combines WebSocket delivery with database persistence:
- Real-time delivery via WebSocket
- Persistent storage for inbox system
- Signal filtering and pagination
- Read/unread status management

### 5. Signal Activities (`activity/websocket_signals.py`)

Temporal activities for sending signals from workflows:
- `send_workflow_signal_activity`
- `send_status_update_activity`
- `send_progress_signal_activity`
- `send_completion_signal_activity`
- `send_error_signal_activity`

### 6. Inbox API (`service/routes_inbox.py`)

REST API for managing signals:
- `GET /api/v1/inbox/signals` - Get user's signals
- `GET /api/v1/inbox/signals/unread-count` - Get unread count
- `POST /api/v1/inbox/signals/{id}/read` - Mark as read
- `POST /api/v1/inbox/signals/mark-all-read` - Mark all as read

## Signal Types

### 1. Status Update
```json
{
  "signal_type": "status_update",
  "workflow_id": "doc-123",
  "data": {
    "status": "processing",
    "message": "Document processing started",
    "progress": 0.3
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. Progress Update
```json
{
  "signal_type": "progress",
  "workflow_id": "doc-123",
  "data": {
    "progress": 0.5,
    "step": "Generating embeddings",
    "message": "Creating vector embeddings"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3. Completion
```json
{
  "signal_type": "completion",
  "workflow_id": "doc-123",
  "data": {
    "result": {
      "status": "completed",
      "document_id": "doc-123",
      "text_length": 5000,
      "chunk_count": 25
    },
    "message": "Document processing completed successfully"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 4. Error
```json
{
  "signal_type": "error",
  "workflow_id": "doc-123",
  "data": {
    "error": "Failed to extract text from document",
    "error_code": "EXTRACTION_ERROR"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Database Schema

### workflow_signals Table

```sql
CREATE TABLE workflow_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workflow_id TEXT NOT NULL,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('status_update', 'completion', 'error', 'progress')),
    data JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_workflow_signals_user_id` - User queries
- `idx_workflow_signals_workflow_id` - Workflow queries
- `idx_workflow_signals_read` - Unread queries
- `idx_workflow_signals_user_created` - User inbox queries

## Frontend Integration

### WebSocket Client Setup

```typescript
interface WebSocketSignal {
  signal_type: 'status_update' | 'completion' | 'error' | 'progress';
  workflow_id: string;
  data: any;
  timestamp: string;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string) {
    const wsUrl = `wss://api.hey.sh/ws?token=${token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const signal: WebSocketSignal = JSON.parse(event.data);
      this.handleSignal(signal);
    };
    
    this.ws.onclose = () => {
      this.handleReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
        this.connect(this.getToken());
      }, delay);
    }
  }

  private handleSignal(signal: WebSocketSignal) {
    // Handle different signal types
    switch (signal.signal_type) {
      case 'status_update':
        this.handleStatusUpdate(signal);
        break;
      case 'progress':
        this.handleProgress(signal);
        break;
      case 'completion':
        this.handleCompletion(signal);
        break;
      case 'error':
        this.handleError(signal);
        break;
    }
  }
}
```

### Inbox Integration

```typescript
// Get user's signals
const getSignals = async (limit = 50, offset = 0) => {
  const response = await fetch('/api/v1/inbox/signals', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return response.json();
};

// Mark signal as read
const markAsRead = async (signalId: string) => {
  await fetch(`/api/v1/inbox/signals/${signalId}/read`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
};

// Get unread count
const getUnreadCount = async () => {
  const response = await fetch('/api/v1/inbox/signals/unread-count', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.json();
};
```

## Workflow Integration

### Updated Document Processing Workflow

The `DocumentProcessingWorkflow` now includes WebSocket signals at each step:

```python
@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, document_id: str, domain_id: str, file_path: str, user_id: str):
        workflow_id = workflow.info().workflow_id
        
        # Send initial status
        await workflow.execute_activity(
            send_status_update_activity,
            args=[user_id, workflow_id, "started", "Document processing started"],
        )
        
        # Process document with progress updates
        await workflow.execute_activity(
            send_progress_signal_activity,
            args=[user_id, workflow_id, 0.1, "Downloading document"],
        )
        
        # ... document processing steps ...
        
        # Send completion
        await workflow.execute_activity(
            send_completion_signal_activity,
            args=[user_id, workflow_id, result, "Processing completed"],
        )
```

## Deployment

### 1. Database Migration

Run the signal table creation script:
```bash
psql -h your-db-host -U your-user -d your-database -f script/create_signal_table.sql
```

### 2. Environment Variables

```bash
# WebSocket configuration
WEBSOCKET_ENABLED=true
WEBSOCKET_CORS_ORIGINS=https://your-frontend-domain.com

# Database (already configured)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### 3. Worker Registration

The WebSocket signal activities are automatically registered in the worker:

```python
# worker/main.py
activities=[
    # ... existing activities ...
    # WebSocket signal activities
    send_workflow_signal_activity,
    send_status_update_activity,
    send_progress_signal_activity,
    send_completion_signal_activity,
    send_error_signal_activity,
]
```

## Testing

### 1. WebSocket Connection Test

```bash
# Test WebSocket connection
python test_websocket_integration.py
```

### 2. Manual Testing

```bash
# Test WebSocket endpoint
curl "http://localhost:8000/ws/status"

# Test inbox API (requires authentication)
curl -H "Authorization: Bearer your-jwt-token" \
     "http://localhost:8000/api/v1/inbox/signals"
```

### 3. Frontend Testing

```javascript
// Test WebSocket connection
const ws = new WebSocket('wss://api.hey.sh/ws?token=your-jwt-token');
ws.onmessage = (event) => {
  console.log('Received signal:', JSON.parse(event.data));
};
```

## Monitoring

### 1. WebSocket Status

```bash
GET /ws/status
```

Returns:
```json
{
  "total_connections": 15,
  "connected_users": ["user-1", "user-2"],
  "user_connection_counts": {
    "user-1": 2,
    "user-2": 1
  }
}
```

### 2. Signal Metrics

Monitor signal delivery:
- WebSocket delivery success rate
- Database persistence success rate
- Signal processing latency
- Connection health

### 3. Error Handling

- Failed WebSocket deliveries are logged
- Database persistence failures are logged
- Connection cleanup on errors
- Automatic reconnection on frontend

## Security

### 1. Authentication

- JWT token validation for WebSocket connections
- User-specific signal routing
- Row-level security on signal table

### 2. Authorization

- Users can only see their own signals
- Service role can insert signals
- No cross-user signal access

### 3. Data Protection

- Signal data is encrypted in transit (WSS)
- Sensitive data is not logged
- Automatic cleanup of old signals

## Performance

### 1. Connection Management

- Efficient user-to-connections mapping
- Automatic cleanup of dead connections
- Connection pooling for high concurrency

### 2. Database Optimization

- Indexed queries for fast signal retrieval
- Pagination for large signal lists
- Automatic cleanup of old signals

### 3. Scalability

- Horizontal scaling with multiple API instances
- Database-backed signal persistence
- Stateless WebSocket connections

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check JWT token validity
   - Verify CORS configuration
   - Check network connectivity

2. **Signals Not Received**
   - Verify user authentication
   - Check workflow execution
   - Monitor signal delivery logs

3. **Database Errors**
   - Check database connectivity
   - Verify table permissions
   - Monitor query performance

### Debug Commands

```bash
# Check WebSocket status
curl http://localhost:8000/ws/status

# Test signal delivery
curl -X POST http://localhost:8000/ws/send-test \
     -d '{"user_id": "test-user", "message": "Test signal"}'

# Check database
psql -c "SELECT COUNT(*) FROM workflow_signals;"
```

## Future Enhancements

1. **Signal Filtering**: Advanced filtering by signal type, workflow, date
2. **Signal Batching**: Batch multiple signals for efficiency
3. **Signal Templates**: Predefined signal templates for common workflows
4. **Analytics**: Signal delivery metrics and user engagement
5. **Push Notifications**: Mobile push notifications for critical signals

---

This WebSocket integration provides a robust, scalable solution for real-time communication between Temporal workflows and the frontend, with comprehensive persistence and inbox functionality.
