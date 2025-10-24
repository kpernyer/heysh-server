---
id: add-temporal-workflow
version: 1
audience: "Claude|Cursor|Cline"
purpose: "Create a new Temporal workflow following hey.sh conventions"
---

# Create New Temporal Workflow

Create a new Temporal workflow that follows hey.sh architectural conventions.

## Requirements

### File Structure
- Location: `backend/workflow/{workflow_name}.py`
- Must import activities from: `backend/activity/`
- May import shared code from: `backend/src/app/`
- Must NOT import from: `backend/service/` or `backend/worker/`

### Code Requirements
1. Use `@workflow.defn` decorator on the workflow class
2. Use `@workflow.run` decorator on the run method
3. Include proper type hints (mypy compliant)
4. Add structured logging with `workflow.logger`
5. Implement error handling with try/except
6. Use `workflow.execute_activity()` with proper timeouts and retry policies
7. Return a dictionary with results and metadata

### Retry Policy
All activities should have retry policies:
```python
retry_policy=workflow.RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)
```

### Timeouts
Set appropriate `start_to_close_timeout` for each activity:
- Quick operations: 1-2 minutes
- API calls: 2-5 minutes
- File processing: 5-10 minutes

## Template

```python
"""[Workflow description]

Orchestrates the [purpose] pipeline:
1. [Step 1]
2. [Step 2]
3. [Step 3]
"""

from datetime import timedelta
from typing import Any

import structlog
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activity.[module] import (
        [activity_name],
    )

logger = structlog.get_logger()


@workflow.defn
class [WorkflowName]Workflow:
    """[Brief workflow description]."""

    @workflow.run
    async def run(self, param1: str, param2: str) -> dict[str, Any]:
        """
        [Detailed workflow description].

        Args:
            param1: [Description]
            param2: [Description]

        Returns:
            Dictionary with workflow results
        """
        workflow.logger.info(
            "Starting [workflow name]",
            param1=param1,
            param2=param2,
        )

        try:
            # Step 1: [Description]
            result1 = await workflow.execute_activity(
                [activity_name],
                args=[param1],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            # Add more steps...

            workflow.logger.info("[Workflow name] completed successfully")

            return {
                "status": "completed",
                "result": result1,
            }

        except Exception as e:
            workflow.logger.error(
                "[Workflow name] failed",
                error=str(e),
            )
            raise
```

## Testing

Create corresponding test file at `backend/test/workflow/test_{workflow_name}.py`:

```python
import pytest
from temporalio.testing import WorkflowEnvironment
from workflow.[workflow_name] import [WorkflowName]Workflow


@pytest.mark.asyncio
async def test_[workflow_name]_workflow():
    """Test [workflow name] workflow."""
    async with await WorkflowEnvironment.start_local() as env:
        # Test implementation
        pass
```

## Registration

Add workflow to `backend/worker/main.py`:
```python
from workflow import [WorkflowName]Workflow

worker = Worker(
    client,
    task_queue=task_queue,
    workflows=[
        # ... existing workflows
        [WorkflowName]Workflow,
    ],
    # ...
)
```

## Documentation

Add workflow description to `docs/workflows.md` with:
- Purpose
- Input parameters
- Expected output
- Error handling
- Example usage
