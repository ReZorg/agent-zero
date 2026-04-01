"""Tests for helpers/functions.py – the safe_call utility."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from helpers.functions import safe_call


# ---------------------------------------------------------------------------
# Basic positional-argument handling
# ---------------------------------------------------------------------------

class TestPositionalArgs:
    def test_exact_args_match(self):
        def f(a, b):
            return a + b

        assert safe_call(f, 3, 4) == 7

    def test_extra_args_are_dropped(self):
        def f(a):
            return a * 2

        # Extra positional args should be silently discarded
        result = safe_call(f, 5, 99, 100)
        assert result == 10

    def test_no_args_function(self):
        def f():
            return "hello"

        assert safe_call(f) == "hello"

    def test_extra_args_on_no_arg_function(self):
        def f():
            return 42

        assert safe_call(f, 1, 2, 3) == 42

    def test_missing_positional_uses_defaults(self):
        def f(a, b=10):
            return a + b

        result = safe_call(f, 1)
        assert result == 11

    def test_single_positional_arg(self):
        def f(x):
            return x ** 2

        assert safe_call(f, 7) == 49


# ---------------------------------------------------------------------------
# VAR_POSITIONAL (*args)
# ---------------------------------------------------------------------------

class TestVarPositional:
    def test_var_args_receives_all(self):
        def f(*args):
            return sum(args)

        assert safe_call(f, 1, 2, 3, 4) == 10

    def test_var_args_empty(self):
        def f(*args):
            return len(args)

        assert safe_call(f) == 0

    def test_mixed_positional_and_var_args(self):
        def f(a, *args):
            return a, args

        result = safe_call(f, 1, 2, 3)
        assert result == (1, (2, 3))


# ---------------------------------------------------------------------------
# Keyword-argument handling
# ---------------------------------------------------------------------------

class TestKwargs:
    def test_exact_kwargs_match(self):
        def f(a, b):
            return a - b

        assert safe_call(f, a=10, b=3) == 7

    def test_unknown_kwargs_filtered_out(self):
        def f(a):
            return a + 1

        result = safe_call(f, a=5, unknown=99)
        assert result == 6

    def test_all_unknown_kwargs_filtered(self):
        def f():
            return "ok"

        assert safe_call(f, garbage=True, more="stuff") == "ok"

    def test_partial_kwargs_accepted(self):
        def f(a, b=0, c=0):
            return a + b + c

        result = safe_call(f, a=1, b=2, ignored=42)
        assert result == 3


# ---------------------------------------------------------------------------
# VAR_KEYWORD (**kwargs)
# ---------------------------------------------------------------------------

class TestVarKeyword:
    def test_var_kwargs_receives_all(self):
        def f(**kwargs):
            return sorted(kwargs.keys())

        result = safe_call(f, x=1, y=2, z=3)
        assert result == ["x", "y", "z"]

    def test_var_kwargs_empty(self):
        def f(**kwargs):
            return len(kwargs)

        assert safe_call(f) == 0

    def test_mixed_positional_and_var_kwargs(self):
        def f(a, **kwargs):
            return a, kwargs

        result = safe_call(f, 1, b=2, c=3)
        assert result == (1, {"b": 2, "c": 3})


# ---------------------------------------------------------------------------
# Combined *args and **kwargs
# ---------------------------------------------------------------------------

class TestCombined:
    def test_accepts_all_args_and_kwargs(self):
        def f(*args, **kwargs):
            return args, kwargs

        result = safe_call(f, 1, 2, x="a")
        assert result == ((1, 2), {"x": "a"})

    def test_positional_and_named_mix(self):
        def f(a, b, c=10):
            return a + b + c

        # Pass extra positional and an extra kwarg
        result = safe_call(f, 1, 2, extra="ignored")
        assert result == 13  # 1+2+10


# ---------------------------------------------------------------------------
# Return value passthrough
# ---------------------------------------------------------------------------

class TestReturnValue:
    def test_returns_none(self):
        def f():
            pass

        assert safe_call(f) is None

    def test_returns_complex_object(self):
        def f(data):
            return {"result": data}

        assert safe_call(f, [1, 2, 3]) == {"result": [1, 2, 3]}
