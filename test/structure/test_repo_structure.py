"""Test repository structure compliance."""

from pathlib import Path


class TestRepoStructure:
    """Test repository structure."""

    def test_required_directories_exist(self) -> None:
        """Test that all required directories exist."""
        repo_root = Path(__file__).parent.parent.parent
        required_dirs = [
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

        for dir_name in required_dirs:
            dir_path = repo_root / dir_name
            assert dir_path.exists(), f"Missing directory: {dir_name}/"
            assert dir_path.is_dir(), f"'{dir_name}' is not a directory"

    def test_prompt_subdirectories_exist(self) -> None:
        """Test that prompt subdirectories exist."""
        repo_root = Path(__file__).parent.parent.parent
        prompt_dir = repo_root / "prompt"

        assert (prompt_dir / "coding").exists()
        assert (prompt_dir / "api-calling").exists()

    def test_src_app_structure(self) -> None:
        """Test src/app/ structure."""
        repo_root = Path(__file__).parent.parent.parent
        src_app = repo_root / "src" / "app"

        required_subdirs = ["clients", "models", "schemas", "utils"]

        for subdir in required_subdirs:
            assert (src_app / subdir).exists(), f"Missing src/app/{subdir}/"
