import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models

ex1 = "<think>reasoning goes here</think>response goes here"
ex2 = "<think>reasoning goes here</thi"


import pytest


@pytest.mark.parametrize("example", [ex1, ex2])
def test_example(example: str):
    res = models.ChatGenerationResult()
    for i in range(len(example)):
        char = example[i]
        chunk = res.add_chunk({"response_delta": char, "reasoning_delta": ""})
        print(i, ":", chunk)

    print("output", res.output())


# ---------------------------------------------------------------------------
# Helper: feed a full string in one shot
# ---------------------------------------------------------------------------

def _feed(text: str, reasoning_delta: str = "") -> models.ChatGenerationResult:
    res = models.ChatGenerationResult()
    res.add_chunk({"response_delta": text, "reasoning_delta": reasoning_delta})
    return res


def _feed_char_by_char(text: str) -> models.ChatGenerationResult:
    res = models.ChatGenerationResult()
    for char in text:
        res.add_chunk({"response_delta": char, "reasoning_delta": ""})
    return res


# ---------------------------------------------------------------------------
# No thinking tags – everything lands in response
# ---------------------------------------------------------------------------

class TestNoThinkingTags:
    def test_plain_response_no_tags(self):
        res = _feed("hello world")
        out = res.output()
        assert out["response_delta"] == "hello world"
        assert out["reasoning_delta"] == ""

    def test_empty_input(self):
        res = _feed("")
        out = res.output()
        assert out["response_delta"] == ""
        assert out["reasoning_delta"] == ""

    def test_response_preserved_without_tags(self):
        text = "This is a plain answer."
        res = _feed(text)
        assert res.output()["response_delta"] == text


# ---------------------------------------------------------------------------
# Complete <think>...</think> block
# ---------------------------------------------------------------------------

class TestCompleteThinkTags:
    def test_think_block_extracted_as_reasoning(self):
        res = _feed("<think>I am reasoning</think>Final answer")
        out = res.output()
        assert "I am reasoning" in out["reasoning_delta"]
        assert "Final answer" in out["response_delta"]
        assert "<think>" not in out["response_delta"]
        assert "</think>" not in out["response_delta"]

    def test_reasoning_block_extracted(self):
        res = _feed("<reasoning>deep thought</reasoning>answer here")
        out = res.output()
        assert "deep thought" in out["reasoning_delta"]
        assert "answer here" in out["response_delta"]

    def test_no_response_after_think_block(self):
        res = _feed("<think>only reasoning</think>")
        out = res.output()
        assert "only reasoning" in out["reasoning_delta"]
        assert out["response_delta"] == ""

    def test_no_reasoning_only_response(self):
        res = _feed("only response, no tags")
        out = res.output()
        assert out["reasoning_delta"] == ""
        assert "only response" in out["response_delta"]

    def test_char_by_char_complete_think(self):
        res = _feed_char_by_char("<think>reason</think>result")
        out = res.output()
        assert "reason" in out["reasoning_delta"]
        assert "result" in out["response_delta"]


# ---------------------------------------------------------------------------
# Truncated / partial closing tag
# ---------------------------------------------------------------------------

class TestPartialClosingTag:
    def test_partial_closing_tag_held_in_unprocessed(self):
        # Feed up to just before the complete </think>
        res = _feed("<think>reasoning goes here</thi")
        out = res.output()
        # Partial closing tag should be buffered, reasoning accumulated
        assert "reasoning goes here" in out["reasoning_delta"]

    def test_char_by_char_partial_closing(self):
        res = _feed_char_by_char("<think>reasoning goes here</thi")
        out = res.output()
        assert "reasoning goes here" in out["reasoning_delta"]


# ---------------------------------------------------------------------------
# Partial opening tag buffering
# ---------------------------------------------------------------------------

class TestPartialOpeningTag:
    def test_partial_opening_tag_is_buffered(self):
        # Send "<thi" – looks like the start of <think>
        res = _feed("<thi")
        out = res.output()
        # Should be buffered in unprocessed, not emitted as response yet
        # Output will include it one way or another (either response or unprocessed)
        total = out["response_delta"] + out["reasoning_delta"]
        assert "thi" in total

    def test_complete_after_partial_opening(self):
        res = models.ChatGenerationResult()
        # Send partial opening tag then complete it
        res.add_chunk({"response_delta": "<thi", "reasoning_delta": ""})
        res.add_chunk({"response_delta": "nk>reason</think>done", "reasoning_delta": ""})
        out = res.output()
        assert "reason" in out["reasoning_delta"]
        assert "done" in out["response_delta"]


# ---------------------------------------------------------------------------
# Native reasoning (reasoning_delta channel)
# ---------------------------------------------------------------------------

class TestNativeReasoning:
    def test_native_reasoning_flag_set(self):
        res = models.ChatGenerationResult()
        res.add_chunk({"response_delta": "answer", "reasoning_delta": "native thought"})
        assert res.native_reasoning is True

    def test_native_reasoning_delta_accumulated(self):
        res = _feed("answer", reasoning_delta="thought")
        assert "thought" in res.output()["reasoning_delta"]

    def test_native_reasoning_response_not_affected(self):
        res = _feed("answer", reasoning_delta="thought")
        assert "answer" in res.output()["response_delta"]

    def test_native_reasoning_ignores_think_tags(self):
        # When native reasoning is used, think tags in response_delta are NOT parsed
        res = models.ChatGenerationResult()
        res.add_chunk({"response_delta": "", "reasoning_delta": "native"})
        res.add_chunk({"response_delta": "<think>tag</think>text", "reasoning_delta": ""})
        out = res.output()
        # Tags are left as-is in response because native_reasoning=True
        assert "<think>" in out["response_delta"]
        assert "native" in out["reasoning_delta"]

    def test_native_reasoning_not_set_without_reasoning_delta(self):
        res = _feed("just a response")
        assert res.native_reasoning is False


# ---------------------------------------------------------------------------
# output() method
# ---------------------------------------------------------------------------

class TestOutput:
    def test_output_returns_chat_chunk(self):
        res = _feed("test")
        out = res.output()
        assert "response_delta" in out
        assert "reasoning_delta" in out

    def test_output_unprocessed_goes_to_response_when_no_reasoning(self):
        # Partial opening tag with no reasoning yet → ends up in response
        res = _feed("<nope")
        out = res.output()
        assert out["response_delta"] != "" or out["reasoning_delta"] != ""

    def test_output_unprocessed_appended_to_reasoning_when_only_reasoning(self):
        # Reasoning accumulated, then a partial close tag remains in unprocessed
        res = _feed_char_by_char("<think>thought</thi")
        out = res.output()
        # reasoning should have "thought" and the partial close should be appended
        assert "thought" in out["reasoning_delta"]


# ---------------------------------------------------------------------------
# Multiple chunks / multi-call accumulation
# ---------------------------------------------------------------------------

class TestMultipleChunks:
    def test_response_accumulates_across_chunks(self):
        res = models.ChatGenerationResult()
        res.add_chunk({"response_delta": "part1 ", "reasoning_delta": ""})
        res.add_chunk({"response_delta": "part2 ", "reasoning_delta": ""})
        res.add_chunk({"response_delta": "part3", "reasoning_delta": ""})
        out = res.output()
        assert "part1 part2 part3" in out["response_delta"]

    def test_reasoning_accumulates_across_chunks(self):
        res = models.ChatGenerationResult()
        res.add_chunk({"response_delta": "", "reasoning_delta": "reas1 "})
        res.add_chunk({"response_delta": "", "reasoning_delta": "reas2"})
        out = res.output()
        assert "reas1 reas2" in out["reasoning_delta"]

    def test_add_chunk_returns_processed_chunk(self):
        res = models.ChatGenerationResult()
        returned = res.add_chunk({"response_delta": "hello", "reasoning_delta": ""})
        assert "response_delta" in returned
        assert "reasoning_delta" in returned


if __name__ == "__main__":
    # test_example(ex1)
    test_example(ex2)
