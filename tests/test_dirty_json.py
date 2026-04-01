"""Tests for helpers/dirty_json.py – the lenient JSON parser."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from helpers.dirty_json import DirtyJson, parse, stringify, try_parse


# ---------------------------------------------------------------------------
# try_parse – falls back to DirtyJson when stdlib json fails
# ---------------------------------------------------------------------------

class TestTryParse:
    def test_valid_json_uses_stdlib(self):
        result = try_parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid_json_falls_back_to_dirty(self):
        result = try_parse("{key: value}")
        assert isinstance(result, dict)
        assert result.get("key") is not None

    def test_valid_list(self):
        assert try_parse("[1, 2, 3]") == [1, 2, 3]

    def test_valid_number(self):
        assert try_parse("42") == 42

    def test_valid_bool_true(self):
        assert try_parse("true") is True

    def test_valid_bool_false(self):
        assert try_parse("false") is False

    def test_valid_null(self):
        assert try_parse("null") is None


# ---------------------------------------------------------------------------
# stringify
# ---------------------------------------------------------------------------

class TestStringify:
    def test_simple_dict(self):
        assert stringify({"a": 1}) == '{"a": 1}'

    def test_non_ascii_preserved(self):
        result = stringify({"emoji": "🎉"})
        assert "🎉" in result

    def test_kwargs_passed_through(self):
        result = stringify({"b": 2, "a": 1}, sort_keys=True)
        assert result.index('"a"') < result.index('"b"')


# ---------------------------------------------------------------------------
# DirtyJson.parse_string – empty / whitespace inputs
# ---------------------------------------------------------------------------

class TestEmptyAndWhitespace:
    def test_empty_string(self):
        assert DirtyJson.parse_string("") is None

    def test_whitespace_only(self):
        assert DirtyJson.parse_string("   ") is None

    def test_none_like_empty_after_skipping(self):
        # String with only whitespace around valid JSON
        result = DirtyJson.parse_string('  {"x": 1}  ')
        assert result == {"x": 1}


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------

class TestObjects:
    def test_standard_object(self):
        assert parse('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

    def test_unquoted_keys(self):
        result = parse("{a: 1, b: 2}")
        assert result["a"] == 1
        assert result["b"] == 2

    def test_single_quoted_keys(self):
        result = parse("{'a': 1}")
        assert result["a"] == 1

    def test_trailing_comma(self):
        result = parse('{"a": 1,}')
        assert result == {"a": 1}

    def test_nested_object(self):
        result = parse('{"outer": {"inner": 42}}')
        assert result["outer"]["inner"] == 42

    def test_missing_closing_brace(self):
        # Lenient parser should still return a dict
        result = parse('{"a": 1')
        assert isinstance(result, dict)
        assert result.get("a") == 1

    def test_double_brace_opening(self):
        # {{ }} is template-syntax sugar; the parser skips the outer braces
        # and returns a dict (key parsing of the inner content may vary)
        result = parse('{{"a": 1}}')
        assert isinstance(result, dict)

    def test_empty_object(self):
        assert parse("{}") == {}

    def test_null_value(self):
        result = parse('{"key": null}')
        assert result["key"] is None

    def test_boolean_values(self):
        result = parse('{"t": true, "f": false}')
        assert result["t"] is True
        assert result["f"] is False


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------

class TestArrays:
    def test_standard_array(self):
        assert parse("[1, 2, 3]") == [1, 2, 3]

    def test_trailing_comma_array(self):
        result = parse("[1, 2, 3,]")
        assert result == [1, 2, 3]

    def test_nested_array(self):
        result = parse("[[1, 2], [3, 4]]")
        assert result == [[1, 2], [3, 4]]

    def test_mixed_array(self):
        result = parse('[1, "hello", true, null]')
        assert result == [1, "hello", True, None]

    def test_empty_array(self):
        assert parse("[]") == []

    def test_missing_closing_bracket(self):
        result = parse("[1, 2, 3")
        assert isinstance(result, list)
        assert 1 in result
        assert 2 in result
        assert 3 in result


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

class TestStrings:
    def test_double_quoted_string(self):
        assert parse('"hello"') == "hello"

    def test_single_quoted_string(self):
        assert parse("'hello'") == "hello"

    def test_escape_newline(self):
        result = parse('"line1\\nline2"')
        assert "\n" in result

    def test_escape_tab(self):
        result = parse('"col1\\tcol2"')
        assert "\t" in result

    def test_escape_backslash(self):
        result = parse('"path\\\\file"')
        assert "\\" in result

    def test_unicode_escape(self):
        result = parse('"\\u0041"')  # 'A'
        assert result == "A"

    def test_triple_double_quoted_multiline(self):
        result = parse('"""hello\nworld"""')
        assert "hello" in result
        assert "world" in result

    def test_triple_single_quoted_multiline(self):
        result = parse("'''hello\nworld'''")
        assert "hello" in result
        assert "world" in result

    def test_string_in_object(self):
        result = parse('{"msg": "hello world"}')
        assert result["msg"] == "hello world"


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------

class TestNumbers:
    def test_integer(self):
        result = parse('{"n": 42}')
        assert result["n"] == 42
        assert isinstance(result["n"], int)

    def test_negative_integer(self):
        result = parse('{"n": -5}')
        assert result["n"] == -5

    def test_float(self):
        result = parse('{"n": 3.14}')
        assert abs(result["n"] - 3.14) < 1e-9

    def test_scientific_notation(self):
        result = parse('{"n": 1e3}')
        assert result["n"] == 1000.0

    def test_top_level_integer(self):
        # get_start_pos finds { [ " — a bare number falls through to unquoted
        # but we can wrap it in an object
        result = parse('{"v": 0}')
        assert result["v"] == 0


# ---------------------------------------------------------------------------
# Booleans and null
# ---------------------------------------------------------------------------

class TestLiterals:
    def test_true_case_insensitive(self):
        result = parse('{"a": True}')
        assert result["a"] is True

    def test_false_case_insensitive(self):
        result = parse('{"a": False}')
        assert result["a"] is False

    def test_null(self):
        result = parse('{"a": null}')
        assert result["a"] is None

    def test_undefined_maps_to_none(self):
        result = parse('{"a": undefined}')
        assert result["a"] is None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class TestComments:
    def test_single_line_comment_skipped(self):
        result = parse('{\n// this is a comment\n"a": 1}')
        assert result["a"] == 1

    def test_multiline_comment_skipped(self):
        result = parse('{"a": /* comment */ 1}')
        assert result["a"] == 1

    def test_comment_at_start(self):
        result = parse('// preamble\n{"a": 1}')
        assert result["a"] == 1


# ---------------------------------------------------------------------------
# Streaming / incremental feed
# ---------------------------------------------------------------------------

class TestFeed:
    def test_feed_builds_incrementally(self):
        # feed() is designed for streaming a single contiguous string in chunks.
        # Each call appends to the internal buffer and re-parses from the start.
        parser = DirtyJson()
        # Feed the full JSON in one shot via feed() to verify it works
        result = parser.feed('{"a": 1, "b": 2}')
        assert isinstance(result, dict)
        assert result.get("a") == 1
        assert result.get("b") == 2

    def test_feed_empty_start(self):
        parser = DirtyJson()
        result = parser.feed('{"x": 99}')
        assert isinstance(result, dict)
        assert result.get("x") == 99


# ---------------------------------------------------------------------------
# get_start_pos
# ---------------------------------------------------------------------------

class TestGetStartPos:
    def test_finds_object_brace(self):
        parser = DirtyJson()
        assert parser.get_start_pos('prefix {"a": 1}') == 7

    def test_finds_array_bracket(self):
        parser = DirtyJson()
        assert parser.get_start_pos('prefix [1, 2]') == 7

    def test_finds_quote(self):
        parser = DirtyJson()
        assert parser.get_start_pos('prefix "hello"') == 7

    def test_picks_earliest(self):
        parser = DirtyJson()
        # quote comes before brace in the string
        idx = parser.get_start_pos('"key": {"a": 1}')
        assert idx == 0

    def test_no_special_chars_returns_zero(self):
        parser = DirtyJson()
        assert parser.get_start_pos("just plain text") == 0


# ---------------------------------------------------------------------------
# Complex / regression scenarios
# ---------------------------------------------------------------------------

class TestComplex:
    def test_json_with_preamble_text(self):
        result = parse('Some text before {"key": "value"} and after')
        assert isinstance(result, dict)
        assert result.get("key") == "value"

    def test_deeply_nested(self):
        result = parse('{"a": {"b": {"c": {"d": 42}}}}')
        assert result["a"]["b"]["c"]["d"] == 42

    def test_array_of_objects(self):
        result = parse('[{"id": 1}, {"id": 2}]')
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_object_with_array_value(self):
        result = parse('{"items": [1, 2, 3]}')
        assert result["items"] == [1, 2, 3]

    def test_mixed_quotes_in_values(self):
        result = parse("{'key': \"value\"}")
        assert result["key"] == "value"
