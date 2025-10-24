"""Pydantic schemas for workflow definitions
Validates YAML workflow definitions and provides type safety
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RetryPolicy(BaseModel):
    """Retry policy for activities"""

    max_attempts: int = Field(ge=1, le=10)
    initial_interval: str | None = None
    backoff_coefficient: float | None = Field(default=None, ge=1.0)
    maximum_interval: str | None = None


class AIAgentConfig(BaseModel):
    """Configuration for AI agent actors"""

    model: str
    capabilities: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)


class HumanConfig(BaseModel):
    """Configuration for human actors"""

    role: str
    notification_channels: list[Literal["email", "in-app", "webhook"]] | None = Field(
        default_factory=lambda: ["email", "in-app"]
    )


class ExternalAPIConfig(BaseModel):
    """Configuration for external API actors"""

    endpoint: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    headers: dict[str, str] | None = None
    authentication: dict[str, Any] | None = None


class Actor(BaseModel):
    """Actor definition - can be AI agent, human, or external API"""

    id: str
    type: Literal["ai-agent", "human", "external-api"]
    name: str
    # Additional fields are stored as extras
    model_config = {"extra": "allow"}

    def get_config(self) -> AIAgentConfig | HumanConfig | ExternalAPIConfig:
        """Get typed config based on actor type"""
        config_data = self.model_dump(exclude={"id", "type", "name"})

        if self.type == "ai-agent":
            return AIAgentConfig(**config_data)
        elif self.type == "human":
            return HumanConfig(**config_data)
        elif self.type == "external-api":
            return ExternalAPIConfig(**config_data)
        else:
            raise ValueError(f"Unknown actor type: {self.type}")


class InputSchema(BaseModel):
    """Input parameter schema"""

    name: str
    type: Literal["string", "number", "boolean", "object", "array"]
    required: bool = True
    description: str | None = None
    default: Any | None = None


class OutputSchema(BaseModel):
    """Output parameter schema"""

    name: str
    type: Literal["string", "number", "boolean", "object", "array"]
    description: str | None = None


class HumanTaskUIField(BaseModel):
    """Field definition for human task UI"""

    name: str
    label: str
    type: Literal["text", "textarea", "select", "checkbox", "radio", "file"]
    options: list[str] | None = None
    required: bool | None = False


class HumanTaskUIConfig(BaseModel):
    """UI configuration for human tasks"""

    form_type: Literal["review-form", "approval-dialog", "custom", "data-entry"]
    timeout: str
    reminder_after: str | None = None
    fields: list[HumanTaskUIField] | None = None


class Activity(BaseModel):
    """Activity definition"""

    id: str
    actor: str  # References actor ID
    activity_type: Literal["temporal-activity", "human-task", "api-call"]
    function: str
    description: str | None = None
    inputs: list[InputSchema] = Field(default_factory=list)
    outputs: list[OutputSchema] = Field(default_factory=list)
    depends_on: list[str] | None = None
    timeout: str | None = None
    retry_policy: RetryPolicy | None = None
    ui_config: HumanTaskUIConfig | None = None

    @field_validator("depends_on")
    @classmethod
    def validate_depends_on(cls, v):
        """Ensure depends_on doesn't contain duplicates"""
        if v and len(v) != len(set(v)):
            raise ValueError("depends_on contains duplicate activity IDs")
        return v


class WorkflowCondition(BaseModel):
    """Conditional branching in workflow"""

    if_: str = Field(alias="if")
    then: str


class WorkflowStep(BaseModel):
    """Single step in workflow execution"""

    step: str  # Activity ID
    on_success: str | None = None
    on_failure: str | None = None
    conditions: list[WorkflowCondition] | None = None

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v, info):
        """If conditions exist, on_success/on_failure shouldn't"""
        if v and (info.data.get("on_success") or info.data.get("on_failure")):
            raise ValueError("Cannot have both conditions and on_success/on_failure")
        return v


class WorkflowDefinitionConfig(BaseModel):
    """Workflow execution definition"""

    start: str  # Activity ID to start with
    steps: list[WorkflowStep]


class WorkflowInfo(BaseModel):
    """Basic workflow metadata"""

    name: str
    description: str | None = None


class WorkflowDefinition(BaseModel):
    """Complete workflow definition from YAML"""

    version: str
    workflow: WorkflowInfo
    actors: list[Actor]
    activities: list[Activity]
    workflow_definition: WorkflowDefinitionConfig

    @field_validator("actors")
    @classmethod
    def validate_unique_actor_ids(cls, v):
        """Ensure all actor IDs are unique"""
        ids = [actor.id for actor in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate actor IDs found")
        return v

    @field_validator("activities")
    @classmethod
    def validate_unique_activity_ids(cls, v):
        """Ensure all activity IDs are unique"""
        ids = [activity.id for activity in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate activity IDs found")
        return v

    def validate_references(self) -> list[str]:
        """Validate all references between actors, activities, and workflow steps.
        Returns list of validation errors.
        """
        errors = []

        actor_ids = {actor.id for actor in self.actors}
        activity_ids = {activity.id for activity in self.activities}

        # Validate actor references in activities
        for activity in self.activities:
            if activity.actor not in actor_ids:
                errors.append(
                    f"Activity '{activity.id}' references undefined actor '{activity.actor}'"
                )

            # Validate dependencies
            if activity.depends_on:
                for dep_id in activity.depends_on:
                    if dep_id not in activity_ids:
                        errors.append(
                            f"Activity '{activity.id}' depends on undefined activity '{dep_id}'"
                        )

        # Validate workflow start
        if self.workflow_definition.start not in activity_ids:
            errors.append(
                f"Workflow start references undefined activity '{self.workflow_definition.start}'"
            )

        # Validate workflow steps
        for step in self.workflow_definition.steps:
            if step.step not in activity_ids:
                errors.append(
                    f"Workflow step references undefined activity '{step.step}'"
                )

            if step.on_success and step.on_success not in activity_ids:
                errors.append(
                    f"Workflow step '{step.step}' on_success references undefined activity '{step.on_success}'"
                )

            if step.on_failure and step.on_failure not in activity_ids:
                errors.append(
                    f"Workflow step '{step.step}' on_failure references undefined activity '{step.on_failure}'"
                )

            if step.conditions:
                for condition in step.conditions:
                    if condition.then not in activity_ids:
                        errors.append(
                            f"Workflow step '{step.step}' condition references undefined activity '{condition.then}'"
                        )

        return errors
