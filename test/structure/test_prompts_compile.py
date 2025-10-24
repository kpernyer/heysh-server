"""Test that all prompts compile correctly."""

from tool.prompt_loader import list_prompts, load_prompt


class TestPromptsCompile:
    """Test prompt compilation."""

    def test_all_prompts_load(self) -> None:
        """Test that all prompt files can be loaded."""
        prompts = list_prompts()

        assert len(prompts) > 0, "No prompts found in prompt/ directory"

        for prompt_file in prompts:
            # Should not raise an exception
            data = load_prompt(prompt_file)
            assert data is not None
            assert isinstance(data, dict)

    def test_api_calling_prompts_have_required_fields(self) -> None:
        """Test that API-calling prompts have required fields."""
        api_prompts = list_prompts("api-calling")

        for prompt_file in api_prompts:
            data = load_prompt(prompt_file)

            # Check required fields
            assert "version" in data, f"{prompt_file}: missing 'version'"
            assert "model" in data, f"{prompt_file}: missing 'model'"

            # Should have either system or user_template
            has_prompt = "system" in data or "user_template" in data
            assert has_prompt, f"{prompt_file}: missing prompt content"

    def test_coding_prompts_have_required_fields(self) -> None:
        """Test that coding prompts have required fields."""
        coding_prompts = list_prompts("coding")

        for prompt_file in coding_prompts:
            data = load_prompt(prompt_file)

            # Check front-matter fields
            assert "id" in data, f"{prompt_file}: missing 'id'"
            assert "version" in data, f"{prompt_file}: missing 'version'"
            assert "audience" in data, f"{prompt_file}: missing 'audience'"
            assert "purpose" in data, f"{prompt_file}: missing 'purpose'"
            assert "content" in data, f"{prompt_file}: missing 'content'"
