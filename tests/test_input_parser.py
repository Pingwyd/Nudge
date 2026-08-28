"""Unit tests for InputParser."""

import pytest
from src.backend.input_parser import InputParser


class TestParsePrefixes:
    """Tests for _parse_prefixes static method."""

    def test_high_priority_prefix(self):
        priority, text, tags = InputParser._parse_prefixes("! Buy groceries")
        assert priority == "high"
        assert text == "Buy groceries"
        assert tags == []

    def test_tag_prefix(self):
        priority, text, tags = InputParser._parse_prefixes("#work Finish report")
        assert priority is None
        assert text == "Finish report"
        assert tags == ["work"]

    def test_priority_and_tag(self):
        priority, text, tags = InputParser._parse_prefixes("! #urgent Buy milk")
        assert priority == "high"
        assert text == "Buy milk"
        assert tags == ["urgent"]

    def test_multiple_tags(self):
        priority, text, tags = InputParser._parse_prefixes("#work #backend #urgent Task")
        assert priority is None
        assert text == "Task"
        assert tags == ["work", "backend", "urgent"]

    def test_simple_text_no_prefixes(self):
        priority, text, tags = InputParser._parse_prefixes("Simple task")
        assert priority is None
        assert text == "Simple task"
        assert tags == []

    def test_exclamation_only_returns_empty(self):
        priority, text, tags = InputParser._parse_prefixes("!")
        assert priority is None
        assert text == ""
        assert tags == []

    def test_hash_only_returns_hash_as_text(self):
        priority, text, tags = InputParser._parse_prefixes("#")
        assert priority is None
        assert text == "#"  # # alone is not a valid tag, stays as text
        assert tags == []

    def test_case_insensitive_tags(self):
        priority, text, tags = InputParser._parse_prefixes("#WORK Task")
        assert tags == ["work"]

    def test_tag_in_middle_of_text(self):
        priority, text, tags = InputParser._parse_prefixes("Buy #urgent milk")
        assert priority is None
        assert text == "Buy milk"
        assert tags == ["urgent"]


class TestParseInput:
    """Tests for parse_input static method."""

    def test_empty_input(self):
        assert InputParser.parse_input("") == []

    def test_none_input(self):
        assert InputParser.parse_input(None) == []

    def test_whitespace_only(self):
        assert InputParser.parse_input("   ") == []

    def test_single_task(self):
        tasks = InputParser.parse_input("Buy groceries")
        assert len(tasks) == 1
        assert tasks[0]["text"] == "Buy groceries"
        assert tasks[0]["done"] is False
        assert tasks[0]["priority"] is None
        assert tasks[0]["tags"] == []

    def test_multiple_sentences(self):
        tasks = InputParser.parse_input("First task. Second task. Third task")
        assert len(tasks) == 3
        assert tasks[0]["text"] == "First task"
        assert tasks[1]["text"] == "Second task"
        assert tasks[2]["text"] == "Third task"

    def test_high_priority_task(self):
        tasks = InputParser.parse_input("! Buy groceries")
        assert len(tasks) == 1
        assert tasks[0]["text"] == "Buy groceries"
        assert tasks[0]["priority"] == "high"

    def test_task_with_tag(self):
        tasks = InputParser.parse_input("#work Finish report")
        assert len(tasks) == 1
        assert tasks[0]["text"] == "Finish report"
        assert tasks[0]["tags"] == ["work"]

    def test_abbreviation_not_sentence_break(self):
        tasks = InputParser.parse_input("Dr. Smith went home. Then he slept.")
        assert len(tasks) == 2
        assert tasks[0]["text"] == "Dr. Smith went home"
        assert tasks[1]["text"] == "Then he slept"

    def test_ellipsis_not_sentence_break(self):
        tasks = InputParser.parse_input("Wait... Then do something.")
        assert len(tasks) == 1
        assert "Wait..." in tasks[0]["text"]

    def test_each_task_has_unique_id(self):
        tasks = InputParser.parse_input("Task one. Task two.")
        assert tasks[0]["id"] != tasks[1]["id"]

    def test_each_task_has_created_at(self):
        tasks = InputParser.parse_input("Task one")
        assert "createdAt" in tasks[0]
        assert tasks[0]["createdAt"] is not None

    def test_task_has_required_fields(self):
        tasks = InputParser.parse_input("Test task")
        assert len(tasks) == 1
        task = tasks[0]
        assert "id" in task
        assert "text" in task
        assert "done" in task
        assert "createdAt" in task
        assert "order" in task
        assert "dueDate" in task
        assert "priority" in task
        assert "tags" in task
        assert "recurrence" in task
