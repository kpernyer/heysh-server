"""Prompt loading and rendering utilities."""

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template


def load_prompt(prompt_path: str) -> dict[str, Any]:
    """Load a prompt template file.

    Args:
        prompt_path: Relative path from prompt/ directory

    Returns:
        Prompt template data

    """
    base_path = Path(__file__).parent.parent.parent.parent / "prompt"
    full_path = base_path / prompt_path

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")

    with open(full_path) as f:
        data = yaml.safe_load(f)

    return data


def render_prompt(
    prompt_template: dict[str, Any], variables: dict[str, Any]
) -> dict[str, Any]:
    """Render a prompt template with variables.

    Args:
        prompt_template: Loaded prompt template
        variables: Variables to substitute

    Returns:
        Rendered prompt

    """
    result = {}

    # Render system prompt
    if "system" in prompt_template:
        system_template = Template(prompt_template["system"])
        result["system"] = system_template.render(**variables)

    # Render user prompt
    if "user_template" in prompt_template:
        user_template = Template(prompt_template["user_template"])
        result["user"] = user_template.render(**variables)

    # Pass through other fields
    for key in ["model", "temperature", "max_tokens", "version"]:
        if key in prompt_template:
            result[key] = prompt_template[key]

    return result
