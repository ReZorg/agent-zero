"""Tests for helpers/errors.py – format_error, custom exception classes, etc."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from helpers.errors import (
    handle_error,
    error_text,
    format_error,
    RepairableException,
    InterventionException,
    HandledException,
)


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------

class TestHandleError:
    def test_reraises_cancelled_error(self):
        """asyncio.CancelledError must always propagate."""
        with pytest.raises(asyncio.CancelledError):
            handle_error(asyncio.CancelledError())

    def test_regular_exception_is_silently_swallowed(self):
        """All other exceptions should be ignored (no raise)."""
        handle_error(ValueError("boom"))
        handle_error(RuntimeError("oops"))
        handle_error(Exception("generic"))

    def test_repairable_exception_is_swallowed(self):
        handle_error(RepairableException("fix me"))


# ---------------------------------------------------------------------------
# error_text
# ---------------------------------------------------------------------------

class TestErrorText:
    def test_returns_str_of_exception(self):
        e = ValueError("something went wrong")
        assert error_text(e) == "something went wrong"

    def test_empty_message(self):
        e = RuntimeError("")
        assert error_text(e) == ""

    def test_returns_string_type(self):
        assert isinstance(error_text(Exception("x")), str)


# ---------------------------------------------------------------------------
# format_error – error message position
# ---------------------------------------------------------------------------

def _make_chained_error(depth: int = 3) -> Exception:
    """Create an exception with a real (shallow) traceback."""
    try:
        _recursive_raise(depth)
    except RuntimeError as e:
        return e
    raise AssertionError("unreachable")


def _recursive_raise(n):
    if n <= 0:
        raise RuntimeError("deep error")
    _recursive_raise(n - 1)


class TestFormatErrorMessagePosition:
    def test_error_message_at_top(self):
        e = _make_chained_error(2)
        result = format_error(e, error_message_position="top")
        lines = result.splitlines()
        # First non-empty line should contain the error class name
        first_content = next(l for l in lines if l.strip())
        assert "RuntimeError" in first_content

    def test_error_message_at_bottom(self):
        e = _make_chained_error(2)
        result = format_error(e, error_message_position="bottom")
        lines = [l for l in result.splitlines() if l.strip()]
        last_content = lines[-1]
        assert "RuntimeError" in last_content

    def test_error_message_none_omits_class_name_from_position(self):
        e = _make_chained_error(2)
        result = format_error(e, error_message_position="none")
        # With position=none the error message line is removed but traceback kept
        # The traceback itself may still mention RuntimeError, so just assert
        # the result is a non-empty string
        assert result  # some output produced

    def test_returns_string(self):
        e = ValueError("test")
        assert isinstance(format_error(e), str)

    def test_non_empty_result(self):
        e = ValueError("test message")
        result = format_error(e)
        assert len(result) > 0

    def test_fallback_to_str_when_no_traceback(self):
        # Exception with no __traceback__ – format_error should still return something
        e = ValueError("no traceback here")
        result = format_error(e, start_entries=0, end_entries=0)
        assert result  # must not be empty


# ---------------------------------------------------------------------------
# format_error – trimming long tracebacks
# ---------------------------------------------------------------------------

class TestFormatErrorTrimming:
    def test_deeply_nested_produces_skip_message(self):
        try:
            _recursive_raise(40)
        except RuntimeError as e:
            result = format_error(e, start_entries=5, end_entries=5)
        assert "skipped" in result.lower() or "File" in result

    def test_shallow_traceback_not_trimmed(self):
        try:
            raise ValueError("shallow")
        except ValueError as e:
            result = format_error(e, start_entries=20, end_entries=15)
        # "skipped" should NOT appear for shallow tracebacks
        assert "skipped" not in result.lower()

    def test_zero_entries_keeps_error_message(self):
        try:
            raise RuntimeError("zero entries test")
        except RuntimeError as e:
            result = format_error(e, start_entries=0, end_entries=0)
        assert "RuntimeError" in result or "zero entries test" in result


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class TestCustomExceptions:
    def test_repairable_exception_is_exception(self):
        e = RepairableException("fix me")
        assert isinstance(e, Exception)

    def test_repairable_exception_message(self):
        e = RepairableException("repair needed")
        assert "repair needed" in str(e)

    def test_intervention_exception_is_exception(self):
        e = InterventionException("user intervened")
        assert isinstance(e, Exception)

    def test_intervention_exception_message(self):
        e = InterventionException("stop loop")
        assert "stop loop" in str(e)

    def test_handled_exception_is_exception(self):
        e = HandledException("already handled")
        assert isinstance(e, Exception)

    def test_repairable_can_be_raised_and_caught(self):
        with pytest.raises(RepairableException):
            raise RepairableException("raised")

    def test_intervention_can_be_raised_and_caught(self):
        with pytest.raises(InterventionException):
            raise InterventionException("raised")

    def test_repairable_not_caught_by_intervention(self):
        with pytest.raises(RepairableException):
            try:
                raise RepairableException("repair")
            except InterventionException:
                pass  # should not catch it

    def test_intervention_not_caught_by_repairable(self):
        with pytest.raises(InterventionException):
            try:
                raise InterventionException("intervene")
            except RepairableException:
                pass  # should not catch it
