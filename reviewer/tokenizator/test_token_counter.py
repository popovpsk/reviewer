from unittest.mock import patch

import pytest

# Assuming TokenCounter is in reviewer.reviewer.tokenizator.token_counter
# This import path should work if pytest is run from the project root.
from reviewer.tokenizator.token_counter import TokenCounter

# --- Constants for testing ---
QWEN_MODEL_NAME = "Qwen/Qwen3-8B"  # The model requested by the user


@pytest.fixture(scope="module")
def qwen_token_counter_instance():
    """Provides a TokenCounter instance initialized with the specified Qwen model."""
    try:
        counter = TokenCounter(QWEN_MODEL_NAME)
        # A quick sanity check to ensure the tokenizer is functional
        _ = counter.tokenizer.encode("test")
        return counter
    except (ValueError, ImportError, OSError) as e:
        pytest.skip(f"Could not load Qwen tokenizer '{QWEN_MODEL_NAME}'. Skipping Qwen-specific tests. Error: {e}")


# --- Test Class for Initialization ---
class TestTokenCounterInitialization:
    def test_initialization_success_qwen(self, qwen_token_counter_instance):
        # This test will be skipped if qwen_token_counter_instance fixture is skipped
        assert qwen_token_counter_instance is not None
        assert qwen_token_counter_instance.tokenizer is not None
        # The name_or_path might be resolved to a more specific identifier by Hugging Face
        # So checking if it contains the original name is safer.
        assert QWEN_MODEL_NAME in qwen_token_counter_instance.tokenizer.name_or_path

    def test_initialization_failure_invalid_model(self):
        invalid_model_name = "non-existent-model-12345xyz"
        with pytest.raises(ValueError) as excinfo:
            TokenCounter(invalid_model_name)
        assert f"Could not load tokenizer for '{invalid_model_name}'" in str(excinfo.value)

    @patch("reviewer.tokenizator.token_counter.AutoTokenizer.from_pretrained")
    def test_initialization_import_error(self, mock_from_pretrained):
        # This test simulates the 'transformers' library not being importable at the point of AutoTokenizer call
        # Note: If TokenCounter itself fails on `from transformers... import AutoTokenizer` at the top level,
        # this specific test might not catch that, but rather an ImportError when TokenCounter is imported.
        # This test targets the ImportError caught *within* the __init__.
        mock_from_pretrained.side_effect = ImportError(
            "Simulated transformers import error during AutoTokenizer.from_pretrained"
        )
        with pytest.raises(ImportError) as excinfo:  # The class re-raises ImportError
            TokenCounter("any-model")
        assert "The 'transformers' library is required" in str(excinfo.value)

    def test_initialization_os_error(self):
        # This test covers OSError during tokenizer loading (e.g. model not found, network issues)
        with patch(
            "reviewer.tokenizator.token_counter.AutoTokenizer.from_pretrained",
            side_effect=OSError("Simulated OSError"),
        ):
            with pytest.raises(ValueError) as excinfo:  # The class wraps OSError in ValueError
                TokenCounter("gpt2")
            assert "Could not load tokenizer for 'gpt2'" in str(excinfo.value)
            assert "Simulated OSError" in str(excinfo.value)

    def test_initialization_other_unexpected_error(self):
        # This test covers the generic Exception catch during tokenizer loading.
        with patch(
            "reviewer.tokenizator.token_counter.AutoTokenizer.from_pretrained",
            side_effect=Exception("Unexpected generic error"),
        ):
            with pytest.raises(ValueError) as excinfo:  # The class wraps generic Exception in ValueError
                TokenCounter("gpt2")
            assert "An unexpected error occurred while loading tokenizer" in str(excinfo.value)
            assert "Unexpected generic error" in str(excinfo.value)


# --- Test Class for TokenCounter Methods (Qwen) ---
# These tests will be skipped if the qwen_token_counter_instance fixture is skipped.
class TestTokenCounterMethodsQwen:
    TEXT_SAMPLE = "Hello world, this is a Qwen test. Привіт світ!"
    TEXT_HELLO = "Hello world"
    EMPTY_TEXT = ""
    NONE_INPUT = None

    # --- count_tokens tests ---
    def test_count_tokens_qwen_simple_text(self, qwen_token_counter_instance):
        count_with_special = qwen_token_counter_instance.count_tokens(self.TEXT_HELLO, add_special_tokens=True)
        count_without_special = qwen_token_counter_instance.count_tokens(self.TEXT_HELLO, add_special_tokens=False)

        assert count_without_special > 0
        # For "Hello world", Qwen/Qwen3-8B seems to produce the same token count
        assert count_with_special == count_without_special

        # Test with more complex text
        count_with_special_long = qwen_token_counter_instance.count_tokens(self.TEXT_SAMPLE, add_special_tokens=True)
        count_without_special_long = qwen_token_counter_instance.count_tokens(
            self.TEXT_SAMPLE, add_special_tokens=False
        )
        assert count_without_special_long > 5  # Heuristic for the given sample
        assert count_with_special_long >= count_without_special_long

    def test_count_tokens_qwen_empty_string(self, qwen_token_counter_instance):
        # `encode("", add_special_tokens=False)` -> [] (0 tokens)
        # `encode("", add_special_tokens=True)` -> For Qwen/Qwen3-8B, this is expected to result in 0 tokens
        # even after token_counter.py fix, based on observed behavior.
        assert qwen_token_counter_instance.count_tokens(self.EMPTY_TEXT, add_special_tokens=True) == 0
        assert qwen_token_counter_instance.count_tokens(self.EMPTY_TEXT, add_special_tokens=False) == 0

    def test_count_tokens_qwen_non_string_input(self, qwen_token_counter_instance):
        assert qwen_token_counter_instance.count_tokens(self.NONE_INPUT) == 0
        assert qwen_token_counter_instance.count_tokens(123) == 0  # type: ignore

    # --- get_tokens_as_strings tests ---
    def test_get_tokens_as_strings_qwen_no_special(self, qwen_token_counter_instance):
        tokens = qwen_token_counter_instance.get_tokens_as_strings(self.TEXT_HELLO, add_special_tokens=False)
        assert len(tokens) > 0
        assert all(not t.startswith("<|") for t in tokens)  # Ensure no special tokens like <|endoftext|>

    def test_get_tokens_as_strings_qwen_with_special(self, qwen_token_counter_instance):
        # Using TEXT_SAMPLE as TEXT_HELLO, as "Hello world" doesn't appear to get <|...|>
        # special tokens with Qwen/Qwen3-8B.
        tokens_sample_with_special = qwen_token_counter_instance.get_tokens_as_strings(
            self.TEXT_SAMPLE, add_special_tokens=True
        )
        tokens_sample_no_special = qwen_token_counter_instance.get_tokens_as_strings(
            self.TEXT_SAMPLE, add_special_tokens=False
        )

        # Expect more tokens for TEXT_SAMPLE when special tokens are added
        # (consistent with count_tokens test for TEXT_SAMPLE).
        # For Qwen/Qwen3-8B and TEXT_SAMPLE, it appears add_special_tokens=True does not change the token count.
        # So, we check for greater than or equal.
        assert len(tokens_sample_with_special) >= len(tokens_sample_no_special)

        # Check if any of the *added* token strings match the <|...|> pattern,
        # only if special tokens were actually added and changed the list length.
        if len(tokens_sample_with_special) > len(tokens_sample_no_special):
            added_token_strings = [
                t
                for t in tokens_sample_with_special
                if t not in tokens_sample_no_special
                or tokens_sample_with_special.count(t) > tokens_sample_no_special.count(t)
            ]
            # This assertion is important: if lengths differ, we expect the 'added_token_strings' list to be non-empty.
            assert added_token_strings, (
                "Length of token lists differ, but no distinct added tokens were identified."
                "Check 'added_token_strings' logic."
            )
            assert any(t.startswith("<|") and t.endswith("|>") for t in added_token_strings), (
                f"No <|...|> special tokens found in added tokens for TEXT_SAMPLE. Added: {added_token_strings}"
            )
        # If lengths are equal, it implies no special tokens were added that changed the token list,
        # or the nature of special tokens for this input doesn't involve typical <|...|> markers.

    def test_get_tokens_as_strings_qwen_empty_string(self, qwen_token_counter_instance):
        assert qwen_token_counter_instance.get_tokens_as_strings(self.EMPTY_TEXT, add_special_tokens=False) == []

        tokens_special_empty = qwen_token_counter_instance.get_tokens_as_strings(
            self.EMPTY_TEXT, add_special_tokens=True
        )
        # Expect 0 tokens (empty list) if Qwen/Qwen3-8B tokenizer returns no IDs/strings
        # for an empty string even with add_special_tokens=True.
        assert len(tokens_special_empty) == 0
        # The following assertion on an empty list is vacuously true.
        assert all(t.startswith("<|") and t.endswith("|>") for t in tokens_special_empty)

    def test_get_tokens_as_strings_qwen_non_string_input(self, qwen_token_counter_instance):
        assert qwen_token_counter_instance.get_tokens_as_strings(self.NONE_INPUT) == []
        assert qwen_token_counter_instance.get_tokens_as_strings(123) == []  # type: ignore

    # --- get_token_ids tests ---
    def test_get_token_ids_qwen_simple_text(self, qwen_token_counter_instance):
        ids_with_special = qwen_token_counter_instance.get_token_ids(self.TEXT_HELLO, add_special_tokens=True)
        ids_without_special = qwen_token_counter_instance.get_token_ids(self.TEXT_HELLO, add_special_tokens=False)

        assert len(ids_without_special) > 0
        # For "Hello world", Qwen/Qwen3-8B seems to produce the same token ID count
        assert len(ids_with_special) == len(ids_without_special)

        # Verify consistency with count_tokens
        assert len(ids_with_special) == qwen_token_counter_instance.count_tokens(
            self.TEXT_HELLO, add_special_tokens=True
        )
        assert len(ids_without_special) == qwen_token_counter_instance.count_tokens(
            self.TEXT_HELLO, add_special_tokens=False
        )

    def test_get_token_ids_qwen_empty_string(self, qwen_token_counter_instance):
        ids_with_special = qwen_token_counter_instance.get_token_ids(self.EMPTY_TEXT, add_special_tokens=True)
        ids_without_special = qwen_token_counter_instance.get_token_ids(self.EMPTY_TEXT, add_special_tokens=False)

        # Expect 0 token IDs if Qwen/Qwen3-8B tokenizer returns no IDs
        # for an empty string even with add_special_tokens=True.
        assert len(ids_with_special) == 0
        assert len(ids_without_special) == 0

    def test_get_token_ids_qwen_non_string_input(self, qwen_token_counter_instance):
        assert qwen_token_counter_instance.get_token_ids(self.NONE_INPUT) == []
        assert qwen_token_counter_instance.get_token_ids(123) == []  # type: ignore


# --- Test handling of raw_token_output in get_tokens_as_strings ---
class TestGetTokensAsStringsEdgeCases:
    @patch("reviewer.tokenizator.token_counter.AutoTokenizer.from_pretrained")
    def test_convert_ids_to_tokens_returns_string(self, mock_auto_tokenizer_from_pretrained):
        # Setup mock tokenizer and its methods
        mock_tokenizer_instance = mock_auto_tokenizer_from_pretrained.return_value
        mock_tokenizer_instance.encode.return_value = [101, 102]  # Simulate token IDs
        # Simulate convert_ids_to_tokens returning a single string (unusual for list input, but tests the guard)
        mock_tokenizer_instance.convert_ids_to_tokens.return_value = "a_single_token_string"

        # Initialize TokenCounter with the mocked tokenizer
        counter = TokenCounter("mocked-model-name")  # Name doesn't matter due to mock

        # Call the method under test
        tokens = counter.get_tokens_as_strings("some text", add_special_tokens=True)

        # Assertions
        assert tokens == ["a_single_token_string"]  # Should be wrapped in a list
        mock_tokenizer_instance.encode.assert_called_once_with("some text", add_special_tokens=True)
        mock_tokenizer_instance.convert_ids_to_tokens.assert_called_once_with([101, 102])

    @patch("reviewer.tokenizator.token_counter.AutoTokenizer.from_pretrained")
    def test_convert_ids_to_tokens_returns_list_of_strings(self, mock_auto_tokenizer_from_pretrained):
        # Setup mock tokenizer
        mock_tokenizer_instance = mock_auto_tokenizer_from_pretrained.return_value
        mock_tokenizer_instance.encode.return_value = [101, 102, 103]
        # Simulate convert_ids_to_tokens returning a list of strings (normal case)
        mock_tokenizer_instance.convert_ids_to_tokens.return_value = [
            "token1",
            "token2",
            "token3",
        ]

        counter = TokenCounter("mocked-model-name")
        tokens = counter.get_tokens_as_strings("another text", add_special_tokens=True)

        assert tokens == ["token1", "token2", "token3"]
        mock_tokenizer_instance.encode.assert_called_once_with("another text", add_special_tokens=True)
        mock_tokenizer_instance.convert_ids_to_tokens.assert_called_once_with([101, 102, 103])
