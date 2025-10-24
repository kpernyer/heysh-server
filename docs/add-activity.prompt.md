---
id: add-temporal-activity
version: 1
audience: "Claude|Cursor|Cline"
purpose: "Create a new Temporal activity following hey.sh conventions"
---

# Create New Temporal Activity

Create a new Temporal activity that follows hey.sh architectural conventions.

## Requirements

### File Structure
- Location: `backend/activity/{category}.py` (group related activities)
- May import from: `backend/src/app/**`
- Must NOT import from: `backend/workflow/`, `backend/service/`, or `backend/worker/`

### Code Requirements
1. Use `@activity.defn` decorator
2. Include proper type hints (mypy compliant)
3. Add structured logging with `activity.logger`
4. Implement error handling with try/except
5. Return meaningful data structures
6. Keep activities focused and single-purpose

### Activity Guidelines
- Activities should be **deterministic** (same inputs = same outputs)
- Avoid long-running operations (use child workflows for those)
- Handle errors gracefully and log them
- Return data that can be serialized (dicts, lists, primitives)

## Template

```python
"""[Activity category] activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.[client] import get_[client]_client

logger = structlog.get_logger()


@activity.defn
async def [activity_name]_activity([params]) -> [return_type]:
    """
    [Activity description].

    Args:
        [param1]: [Description]
        [param2]: [Description]

    Returns:
        [Description of return value]
    """
    activity.logger.info("[Activity name] started", [param1]=[param1])

    try:
        # Get client
        client = get_[client]_client()

        # Perform activity logic
        result = await client.[method]([args])

        activity.logger.info(
            "[Activity name] completed successfully",
            result_count=len(result),
        )

        return result

    except Exception as e:
        activity.logger.error(
            "[Activity name] failed",
            error=str(e),
        )
        raise
```

## Testing

Create test in `backend/test/activity/test_{category}.py`:

```python
import pytest
from activity.[category] import [activity_name]_activity


@pytest.mark.asyncio
async def test_[activity_name]_activity():
    """Test [activity name] activity."""
    # Test implementation
    result = await [activity_name]_activity([params])
    assert result is not None
```

## Registration

Add activity to:
1. `backend/activity/__init__.py`:
```python
from activity.[category] import [activity_name]_activity

__all__ = [
    # ... existing
    "[activity_name]_activity",
]
```

2. `backend/worker/main.py`:
```python
from activity import [activity_name]_activity

worker = Worker(
    client,
    task_queue=task_queue,
    workflows=[...],
    activities=[
        # ... existing activities
        [activity_name]_activity,
    ],
)
```
