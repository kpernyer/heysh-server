#!/usr/bin/env python3
"""Prompt renderer script.

Renders prompt templates with variable substitution.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.utils.prompts import load_prompt, render_prompt


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Render prompt templates with variables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render question-answering prompt
  python script/render_prompt.py prompt/api-calling/question-answering.v1.prompt.yaml \\
    --vars '{"question": "What is Temporal?", "domain_id": "abc123", "context": []}'

  # Render document summarization prompt
  python script/render_prompt.py prompt/api-calling/summarize-document.v1.prompt.yaml \\
    --vars '{"title": "Getting Started", "domain": "docs", "content": "..."}'
        """,
    )

    parser.add_argument(
        "prompt_file",
        help="Path to prompt file (relative to project root or absolute)",
    )

    parser.add_argument(
        "--vars",
        type=str,
        default="{}",
        help="JSON string of variables to substitute (default: {})",
    )

    parser.add_argument(
        "--output",
        choices=["full", "user", "system"],
        default="full",
        help="What to output: full (default), user only, or system only",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )

    args = parser.parse_args()

    try:
        # Parse variables
        try:
            variables = json.loads(args.vars)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing --vars JSON: {e}", file=sys.stderr)
            return 1

        # Load prompt template
        try:
            template = load_prompt(args.prompt_file)
        except FileNotFoundError:
            print(f"❌ Prompt file not found: {args.prompt_file}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ Error loading prompt: {e}", file=sys.stderr)
            return 1

        # Render prompt
        try:
            rendered = render_prompt(template, variables)
        except Exception as e:
            print(f"❌ Error rendering prompt: {e}", file=sys.stderr)
            return 1

        # Output based on format
        if args.format == "json":
            output = {
                "system": rendered.get("system", ""),
                "user": rendered.get("user", ""),
                "model": rendered.get("model", ""),
                "temperature": rendered.get("temperature"),
                "max_tokens": rendered.get("max_tokens"),
            }
            print(json.dumps(output, indent=2))
        else:
            # Text format
            if args.output in ["full", "system"] and "system" in rendered:
                print("=== SYSTEM PROMPT ===")
                print(rendered["system"])
                print()

            if args.output in ["full", "user"] and "user" in rendered:
                if args.output == "full":
                    print("=== USER PROMPT ===")
                print(rendered["user"])
                if args.output == "full":
                    print()

            if args.output == "full":
                print("=== METADATA ===")
                print(f"Model: {rendered.get('model', 'N/A')}")
                print(f"Temperature: {rendered.get('temperature', 'N/A')}")
                print(f"Max Tokens: {rendered.get('max_tokens', 'N/A')}")

        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
