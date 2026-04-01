"""Tests for helpers/guids.py – the generate_id utility."""
import sys
import os
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from helpers.guids import generate_id

ALPHANUM = set(string.ascii_letters + string.digits)


class TestGenerateId:
    def test_default_length_is_8(self):
        assert len(generate_id()) == 8

    def test_custom_length(self):
        for length in [1, 4, 16, 32]:
            assert len(generate_id(length)) == length

    def test_only_alphanumeric_chars(self):
        for _ in range(20):
            gid = generate_id(20)
            assert all(c in ALPHANUM for c in gid), f"Non-alphanumeric char in {gid!r}"

    def test_returns_string(self):
        assert isinstance(generate_id(), str)

    def test_ids_are_unique(self):
        ids = {generate_id() for _ in range(1000)}
        # With 62^8 possible IDs, the probability of a collision in 1000 draws
        # is negligibly small – assert at least 990 unique values.
        assert len(ids) >= 990

    def test_zero_length(self):
        assert generate_id(0) == ""

    def test_large_length(self):
        gid = generate_id(128)
        assert len(gid) == 128
        assert all(c in ALPHANUM for c in gid)

    def test_ids_vary_across_calls(self):
        ids = [generate_id() for _ in range(5)]
        # At least two distinct values among 5 random 8-char IDs (overwhelmingly likely)
        assert len(set(ids)) > 1
