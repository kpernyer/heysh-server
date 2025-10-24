#!/usr/bin/env python3
"""Prompt loader utility.

Loads and validates prompt files from the prompt/ directory.
"""

from pathlib import Path
from typing import Any

import yaml


def load_prompt(prompt_path: str | Path) -> dict[str, Any]:
    """Load a prompt template file.

    Args:
        prompt_path: Path to prompt file (relative to prompt/ or absolute)

    Returns:
        Prompt template data

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        ValueError: If prompt file is invalid

    """
    if isinstance(prompt_path, str):
        prompt_path = Path(prompt_path)

    # If relative path, resolve from prompt/ directory
    if not prompt_path.is_absolute():
        repo_root = Path(__file__).parent.parent
        prompt_path = repo_root / "prompt" / prompt_path

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    # Load based on file extension
    if prompt_path.suffix == ".yaml" or prompt_path.suffix == ".yml":
        return load_yaml_prompt(prompt_path)
    elif prompt_path.suffix == ".md":
        return load_markdown_prompt(prompt_path)
    else:
        raise ValueError(f"Unsupported prompt file type: {prompt_path.suffix}")


def load_yaml_prompt(file_path: Path) -> dict[str, Any]:
    """Load YAML prompt file.

    Expected format:
    ```yaml
    version: 1
    model: claude-3-5-sonnet-20250219
    temperature: 0.3
    max_tokens: 2000
    system: |
      System prompt text
    user_template: |
      User prompt with {{ variables }}
    ```
    """
    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Validate required fields
    required_fields = ["version", "model"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in {file_path}")

    return data


def load_markdown_prompt(file_path: Path) -> dict[str, Any]:
    """Load Markdown prompt file with YAML front-matter.

    Expected format:
    ```markdown
    ---
    id: prompt-id
    version: 1
    audience: "Claude|Cursor"
    purpose: "Description"
    ---

    # Prompt Content

    Rest of the markdown content...
    ```
    """
    with open(file_path) as f:
        content = f.read()

    # Split front-matter and content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter = yaml.safe_load(parts[1])
            body = parts[2].strip()

            return {
                **front_matter,
                "content": body,
            }

    # No front-matter, return as plain content
    return {"content": content}


def list_prompts(prompt_type: str | None = None) -> list[Path]:
    """List all available prompts.

    Args:
        prompt_type: Filter by type ('coding' or 'api-calling'), or None for all

    Returns:
        List of prompt file paths

    """
    repo_root = Path(__file__).parent.parent
    prompt_dir = repo_root / "prompt"

    if not prompt_dir.exists():
        return []

    if prompt_type:
        search_dir = prompt_dir / prompt_type
        if not search_dir.exists():
            return []
        return list(search_dir.glob("*.prompt.*"))
    else:
        # All prompts
        return list(prompt_dir.rglob("*.prompt.*"))


if __name__ == "__main__":
    # Demo usage
    print("Available prompts:")
    for prompt_file in list_prompts():
        print(f"  - {prompt_file.relative_to(Path(__file__).parent.parent)}")
