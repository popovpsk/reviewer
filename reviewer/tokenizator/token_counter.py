from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.tokenization_utils import PreTrainedTokenizer
from transformers.tokenization_utils_fast import PreTrainedTokenizerFast

class TokenCounter:
    """
    A class to count tokens in a string using Hugging Face tokenizers.
    This class is intended for production use to get accurate token counts
    relevant to specific pre-trained language models.
    """

    def __init__(self, model_name_or_path: str):
        """
        Initializes the TokenCounter with a tokenizer from Hugging Face Hub.

        Args:
            model_name_or_path: The identifier of the pre-trained model on Hugging Face Hub
                                (e.g., "bert-base-uncased", "gpt2", "mistralai/Mistral-7B-v0.1")
                                or a path to a local directory containing tokenizer files.

        Raises:
            ValueError: If the tokenizer cannot be loaded (e.g., model not found, network issues).
            ImportError: If the 'transformers' library is not installed.
        """
        try:
            # The `transformers` library needs to be installed.
            # e.g., pip install transformers tokenizers
            self.tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast = AutoTokenizer.from_pretrained(model_name_or_path)
        except ImportError:
            raise ImportError(
                "The 'transformers' library is required to use Hugging Face tokenizers. "
                "Please install it using 'pip install transformers tokenizers'."
            )
        except OSError as e: # Handles model not found, network issues, etc.
            raise ValueError(
                f"Could not load tokenizer for '{model_name_or_path}'. "
                f"Ensure the model identifier is correct, you have an internet connection, "
                f"and if it's a private/gated model, you are logged in via `huggingface-cli login`. "
                f"Original error: {e}"
            )
        except Exception as e: # Catch any other unexpected errors during loading
            raise ValueError(f"An unexpected error occurred while loading tokenizer for '{model_name_or_path}': {e}")

    def count_tokens(self, text: str, add_special_tokens: bool = True) -> int:
        """
        Counts the number of tokens in the given text using the loaded Hugging Face tokenizer.
        This typically corresponds to the number of input IDs the model will receive.

        Args:
            text: The input string to tokenize.
            add_special_tokens: Whether to include special tokens (e.g., [CLS], [SEP], <s>, </s>)
                                in the count, as per the tokenizer's configuration for the model.
                                Defaults to True, which is usually what you need when estimating
                                input length for a model.

        Returns:
            The number of tokens.
        """
        if not isinstance(text, str):
            # Handle cases where text might not be a string, e.g. None or other types
            # Or raise a TypeError, depending on desired strictness.
            # For now, returning 0 for non-string or empty string.
            return 0

        # The `encode` method converts text to a list of token IDs.
        # The length of this list is the token count.
        # `add_special_tokens=True` is often the default and mimics how text is prepared for models.
        token_ids = self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
        return len(token_ids)

    def get_tokens_as_strings(self, text: str, add_special_tokens: bool = False) -> list[str]:
            """
            Tokenizes the text and returns a list of token strings.

            Note: `tokenizer.tokenize()` often does not add special tokens by default.
            If you need special tokens included as strings, consider using
            `self.tokenizer.convert_ids_to_tokens(self.get_token_ids(text, add_special_tokens=True))`.

            Args:
                text: The input string to tokenize.
                add_special_tokens: If True, attempts to include special tokens by encoding and then decoding.
                                    If False (default), uses `tokenizer.tokenize()` which typically
                                    provides cleaner tokens without model-specific additions.

            Returns:
                A list of token strings.
            """
            if not isinstance(text, str):
                # Or raise TypeError, but for now, align with existing behavior for non-string.
                return []
            if not text and not add_special_tokens:
                # If text is empty AND we are not adding special tokens, result is empty.
                return []
            # Otherwise (text is not empty, OR text is empty and we want special tokens), proceed.

            if add_special_tokens:
                token_ids = self.tokenizer.encode(text, add_special_tokens=True)
                # The `convert_ids_to_tokens` method can be typed as returning `Union[str, List[str]]`
                # by type checkers, especially when dealing with overloaded methods on a
                # union of tokenizer types (PreTrainedTokenizer | PreTrainedTokenizerFast).
                # We explicitly handle both potential return types to ensure `tokens` is `List[str]`.
                raw_token_output = self.tokenizer.convert_ids_to_tokens(token_ids)

                if isinstance(raw_token_output, str):
                    # If a single string is returned, wrap it in a list.
                    # This branch might be taken if token_ids were a single int, or if the
                    # type checker conservatively assumes this path from general overload signatures.
                    # For `token_ids` being `List[int]`, `convert_ids_to_tokens` should return `List[str]`.
                    tokens = [raw_token_output]
                else:
                    # If `raw_token_output` is not a string, it's expected to be `List[str]`.
                    # The type checker, after the isinstance check, should infer this.
                    tokens = raw_token_output
            else:
                # `tokenize` usually gives "cleaner" tokens without special ones like [CLS], [SEP]
                # unless they are inherently part of the tokenization of the input string itself.
                # `self.tokenizer.tokenize()` is generally typed as returning `List[str]`.
                tokens = self.tokenizer.tokenize(text)
            return tokens

    def get_token_ids(self, text: str, add_special_tokens: bool = True) -> list[int]:
        """
        Tokenizes the text and returns a list of token IDs.

        Args:
            text: The input string to tokenize.
            add_special_tokens: Whether to include special tokens in the token ID list.
                                Defaults to True.

        Returns:
            A list of token IDs.
        """
        if not isinstance(text, str):
            # Or raise TypeError.
            return []
        if not text and not add_special_tokens:
            # If text is empty AND we are not adding special tokens, result is empty.
            return []
        # Otherwise (text is not empty, OR text is empty and we want special tokens), proceed.

        token_ids = self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
        return token_ids
