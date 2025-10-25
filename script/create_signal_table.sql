-- Create workflow_signals table for WebSocket signal persistence
-- This table stores signals sent to users for the inbox system

CREATE TABLE IF NOT EXISTS workflow_signals (
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

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_workflow_signals_user_id ON workflow_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_signals_workflow_id ON workflow_signals(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_signals_signal_type ON workflow_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_workflow_signals_read ON workflow_signals(read);
CREATE INDEX IF NOT EXISTS idx_workflow_signals_created_at ON workflow_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_workflow_signals_user_read ON workflow_signals(user_id, read);

-- Create composite index for user inbox queries
CREATE INDEX IF NOT EXISTS idx_workflow_signals_user_created ON workflow_signals(user_id, created_at DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE workflow_signals ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own signals
CREATE POLICY "Users can view their own signals" ON workflow_signals
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can update their own signals (for marking as read)
CREATE POLICY "Users can update their own signals" ON workflow_signals
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Service role can insert signals (for workflow activities)
CREATE POLICY "Service role can insert signals" ON workflow_signals
    FOR INSERT WITH CHECK (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_workflow_signals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_workflow_signals_updated_at
    BEFORE UPDATE ON workflow_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_signals_updated_at();

-- Add comments for documentation
COMMENT ON TABLE workflow_signals IS 'Stores WebSocket signals sent to users for real-time workflow updates';
COMMENT ON COLUMN workflow_signals.user_id IS 'ID of the user who should receive the signal';
COMMENT ON COLUMN workflow_signals.workflow_id IS 'Temporal workflow ID that generated the signal';
COMMENT ON COLUMN workflow_signals.signal_type IS 'Type of signal: status_update, completion, error, progress';
COMMENT ON COLUMN workflow_signals.data IS 'JSON payload containing signal data';
COMMENT ON COLUMN workflow_signals.timestamp IS 'When the signal was generated (workflow time)';
COMMENT ON COLUMN workflow_signals.read IS 'Whether the user has read the signal';
COMMENT ON COLUMN workflow_signals.read_at IS 'When the signal was marked as read';
