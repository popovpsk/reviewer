import argparse
from dataclasses import dataclass


class ReviewMode:
    Auto = "auto"
    FileByFile = "file_by_file"
    AllFilesAtOnce = "all_files_at_once"
    PackageByPackage = "package_by_package"


MODEL_BASE_URL = "https://some-url/"
MODEL_API_KEY = "1"
MODEL_NAME = "DeepSeek-R1-671B-AWQ"

FALLBACK_MODEL_BASE_URL = "http://192.168.3.9:8080/v1"
FALLBACK_MODEL_API_KEY = "1"
FALLBACK_MODEL_NAME = "llama-model"


class InferenceProvider:
    BigModel = "big"
    LlamaCpp = "llamacpp"


# Default values for configuration
DEFAULT_INFERENCE_PROVIDER = InferenceProvider.BigModel
DEFAULT_REVIEW_TEST_FILES = True  # Default to True, can be overridden by CLI
DEFAULT_REVIEW_MODE = ReviewMode.Auto

# Other global settings that will be part of the Configuration object
DEFAULT_TRANSLATE_ENABLED = True


@dataclass
class Configuration:
    repo: str
    target_branch: str
    review_test_files: bool = DEFAULT_REVIEW_TEST_FILES
    review_mode: str = DEFAULT_REVIEW_MODE
    inference_provider: str = DEFAULT_INFERENCE_PROVIDER
    translate_enabled: bool = DEFAULT_TRANSLATE_ENABLED
    context_window: int = 16384


def get_configuration() -> Configuration:
    parser = argparse.ArgumentParser(description="Code reviewer using LLM")
    parser.add_argument("repo", type=str, help="Path to the repository to review")
    parser.add_argument("target_branch", type=str, help="Target branch to compare against master")
    parser.add_argument(
        "--review_test_files",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_REVIEW_TEST_FILES,
        help=f"Enable/disable reviewing test files (default: {'enabled' if DEFAULT_REVIEW_TEST_FILES else 'disabled'})",
    )
    parser.add_argument(
        "--review_mode",
        type=str,
        default=DEFAULT_REVIEW_MODE,
        choices=[
            ReviewMode.FileByFile,
            ReviewMode.AllFilesAtOnce,
            ReviewMode.PackageByPackage,
            ReviewMode.Auto,
        ],
        help=f"Review mode (default: {DEFAULT_REVIEW_MODE})",
    )
    parser.add_argument(
        "--inference_provider",
        type=str,
        default=DEFAULT_INFERENCE_PROVIDER,
        choices=[InferenceProvider.BigModel, InferenceProvider.LlamaCpp],
        help=f"Inference provider to use (default: {DEFAULT_INFERENCE_PROVIDER})",
    )
    parser.add_argument(
        "--translate",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_TRANSLATE_ENABLED,
        help=f"Enable/disable translation of review results (default: {'enabled' if DEFAULT_TRANSLATE_ENABLED else 'disabled'})",  # noqa
    )

    args = parser.parse_args()

    return Configuration(
        repo=args.repo,
        target_branch=args.target_branch,
        review_test_files=args.review_test_files,
        review_mode=args.review_mode,
        inference_provider=args.inference_provider,
        translate_enabled=args.translate,
    )
