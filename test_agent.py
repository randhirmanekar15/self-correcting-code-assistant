"""Tests that do not require a running Ollama model."""

from agent import run_code, strip_fences


def test_strip_fences_removes_python_block():
    text = "```python\nprint('hi')\n```"
    assert strip_fences(text) == "print('hi')"


def test_strip_fences_passthrough_when_no_fence():
    assert strip_fences("print('hi')") == "print('hi')"


def test_run_code_success():
    passed, output = run_code("print('hello')")
    assert passed is True
    assert "hello" in output


def test_run_code_failure_captures_error():
    passed, output = run_code("raise ValueError('boom')")
    assert passed is False
    assert "ValueError" in output
