"""Workflow YAML parser and validator
Loads and validates workflow definitions from YAML files
"""

from pathlib import Path
from typing import Any

import yaml

from ..schemas.workflow_schema import WorkflowDefinition


class WorkflowParseError(Exception):
    """Raised when workflow YAML cannot be parsed"""

    pass


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Workflow validation failed: {len(errors)} error(s)")


def parse_workflow_yaml(yaml_string: str) -> WorkflowDefinition:
    """Parse workflow definition from YAML string

    Args:
        yaml_string: YAML content as string

    Returns:
        Validated WorkflowDefinition

    Raises:
        WorkflowParseError: If YAML cannot be parsed
        WorkflowValidationError: If workflow validation fails

    """
    try:
        data = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        raise WorkflowParseError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise WorkflowParseError("YAML must contain a dictionary at root level")

    try:
        workflow = WorkflowDefinition(**data)
    except Exception as e:
        raise WorkflowParseError(f"Failed to parse workflow schema: {e}")

    # Validate references
    errors = workflow.validate_references()
    if errors:
        raise WorkflowValidationError(errors)

    return workflow


def load_workflow_from_file(file_path: Path | str) -> WorkflowDefinition:
    """Load workflow definition from YAML file

    Args:
        file_path: Path to YAML file

    Returns:
        Validated WorkflowDefinition

    Raises:
        FileNotFoundError: If file doesn't exist
        WorkflowParseError: If YAML cannot be parsed
        WorkflowValidationError: If workflow validation fails

    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    yaml_content = path.read_text()
    return parse_workflow_yaml(yaml_content)


def workflow_to_yaml(workflow: WorkflowDefinition) -> str:
    """Convert workflow definition to YAML string

    Args:
        workflow: WorkflowDefinition instance

    Returns:
        YAML string representation

    """
    data = workflow.model_dump(mode="json", exclude_none=True, by_alias=True)

    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
        allow_unicode=True,
    )


def save_workflow_to_file(workflow: WorkflowDefinition, file_path: Path | str) -> None:
    """Save workflow definition to YAML file

    Args:
        workflow: WorkflowDefinition instance
        file_path: Path where to save the file

    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = workflow_to_yaml(workflow)
    path.write_text(yaml_content)


def get_workflow_summary(workflow: WorkflowDefinition) -> dict[str, Any]:
    """Get a summary of workflow definition

    Args:
        workflow: WorkflowDefinition instance

    Returns:
        Dictionary with workflow statistics

    """
    actor_types = {}
    for actor in workflow.actors:
        actor_types[actor.type] = actor_types.get(actor.type, 0) + 1

    activity_types = {}
    for activity in workflow.activities:
        activity_types[activity.activity_type] = (
            activity_types.get(activity.activity_type, 0) + 1
        )

    return {
        "name": workflow.workflow.name,
        "description": workflow.workflow.description,
        "version": workflow.version,
        "stats": {
            "total_actors": len(workflow.actors),
            "actors_by_type": actor_types,
            "total_activities": len(workflow.activities),
            "activities_by_type": activity_types,
            "workflow_steps": len(workflow.workflow_definition.steps),
            "start_activity": workflow.workflow_definition.start,
        },
    }
