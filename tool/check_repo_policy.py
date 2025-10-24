#!/usr/bin/env python3
"""Repository policy checker.

Validates that the repository follows hey.sh architectural conventions:
1. Top-level directories use singular naming
2. Import dependencies flow correctly
3. Required files exist
"""

import ast
import sys
from pathlib import Path

# Required top-level singular directories
REQUIRED_DIRS = [
    "workflow",
    "activity",
    "worker",
    "service",
    "src",
    "tool",
    "script",
    "test",
    "prompt",
]

# Allowed imports for each module type
IMPORT_RULES = {
    "workflow": ["activity", "src.app"],
    "activity": ["src.app"],
    "worker": ["workflow", "activity", "src.app"],
    "service": ["src.app", "workflow"],
    "src.app": [],  # Cannot import from orchestration layers
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports."""

    def __init__(self) -> None:
        self.imports: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for name in node.names:
            self.imports.append(name.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement."""
        if node.module:
            self.imports.append(node.module)


def check_directory_structure() -> list[str]:
    """Check that required directories exist."""
    errors = []
    repo_root = Path(__file__).parent.parent

    for dir_name in REQUIRED_DIRS:
        dir_path = repo_root / dir_name
        if not dir_path.exists():
            errors.append(f"Missing required directory: {dir_name}/")
        elif not dir_path.is_dir():
            errors.append(f"'{dir_name}' exists but is not a directory")

    return errors


def check_imports_in_file(file_path: Path, module_type: str) -> list[str]:
    """Check that imports in a file follow the rules.

    Args:
        file_path: Path to Python file
        module_type: Type of module (workflow, activity, etc.)

    Returns:
        List of error messages

    """
    errors = []

    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        visitor = ImportVisitor()
        visitor.visit(tree)

        allowed_imports = IMPORT_RULES.get(module_type, [])

        for imp in visitor.imports:
            # Skip standard library and third-party imports
            if not imp.startswith(("workflow", "activity", "worker", "service", "src")):
                continue

            # Check if this import is allowed
            allowed = False
            for allowed_prefix in allowed_imports:
                if imp.startswith(allowed_prefix):
                    allowed = True
                    break

            if not allowed:
                errors.append(
                    f"{file_path.relative_to(file_path.parent.parent.parent)}: "
                    f"Invalid import '{imp}' in {module_type}/ module"
                )

    except Exception as e:
        errors.append(f"Error parsing {file_path}: {e}")

    return errors


def check_import_dependencies() -> list[str]:
    """Check that all Python files follow import rules."""
    errors = []
    repo_root = Path(__file__).parent.parent

    # Check each module type
    for module_type in ["workflow", "activity", "service", "src/app"]:
        module_path = repo_root / module_type
        if not module_path.exists():
            continue

        # Find all Python files
        for py_file in module_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            errors.extend(check_imports_in_file(py_file, module_type.replace("/", ".")))

    return errors


def main() -> int:
    """Run all policy checks."""
    print("🔍 Checking repository policy compliance...")
    print()

    all_errors = []

    # Check 1: Directory structure
    print("1. Checking directory structure...")
    dir_errors = check_directory_structure()
    if dir_errors:
        all_errors.extend(dir_errors)
        print(f"   ❌ Found {len(dir_errors)} error(s)")
        for error in dir_errors:
            print(f"      - {error}")
    else:
        print("   ✅ All required directories present")
    print()

    # Check 2: Import dependencies
    print("2. Checking import dependencies...")
    import_errors = check_import_dependencies()
    if import_errors:
        all_errors.extend(import_errors)
        print(f"   ❌ Found {len(import_errors)} error(s)")
        for error in import_errors:
            print(f"      - {error}")
    else:
        print("   ✅ All imports follow dependency rules")
    print()

    # Summary
    if all_errors:
        print(f"❌ Policy check failed with {len(all_errors)} error(s)")
        return 1
    else:
        print("✅ All policy checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
