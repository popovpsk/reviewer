# Assuming Reviewer and DiffFile are accessible via this path structure
# (e.g., PYTHONPATH set to the project root or the directory containing the first 'reviewer' directory)
from reviewer.agents.review import Reviewer
from reviewer.system_utils.diff import DiffFile


# A placeholder class for LLM, as Reviewer requires an LLM instance
# but _make_files_prompt does not use it.
class PlaceholderLLM:
    def generate(self, _: str, prompt: str) -> str:
        # This method won't be called by _make_files_prompt directly
        return "placeholder llm response"


def test_make_files_prompt():
    # 1. Setup
    placeholder_llm = PlaceholderLLM()
    reviewer_instance = Reviewer(llm=placeholder_llm)

    # Test data using the actual DiffFile class
    df1 = DiffFile(
        name="file1.py",
        full_name="path/to/file1.py",
        original_content="print('old content python')",
        diff="diff_content_py",
        # additional_context and tokens_count will use default values
    )
    df2 = DiffFile(
        name="file2.js",
        full_name="another/path/file2.js",
        original_content="console.log('old content js');",
        diff="diff_content_js",
    )

    # --- Test case 1: Multiple diff files ---
    diffs_multiple = [df1, df2]

    # Expected prompt construction for multiple files
    context_template = Reviewer.CONTEXT  # Accessing via class name for clarity

    # Language determination relies on the private method __language_from_extension
    lang_py = reviewer_instance._Reviewer__language_from_extension(df1.name)
    lang_js = reviewer_instance._Reviewer__language_from_extension(df2.name)

    context_df1_str = context_template.format(df1.full_name, lang_py, df1.original_content)
    context_df2_str = context_template.format(df2.full_name, lang_js, df2.original_content)

    expected_combined_context_multiple = context_df1_str + context_df2_str

    expected_diff_section_multiple = f"<DIFF>\n{df1.diff}\n{df2.diff}\n</DIFF>"
    expected_prompt_multiple = (
        f"{expected_combined_context_multiple}\n{expected_diff_section_multiple}\n{Reviewer.PROMPT}"
    )

    actual_prompt_multiple = reviewer_instance._make_files_prompt(diffs_multiple)
    assert actual_prompt_multiple == expected_prompt_multiple

    # --- Test case 2: Empty list of diffs ---
    diffs_empty = []
    expected_context_empty = ""  # context starts as "" and loop is not entered
    expected_diff_section_empty = "<DIFF>\n</DIFF>"  # diff starts as "" and loop is not entered, then formatted
    expected_prompt_empty = f"{expected_context_empty}\n{expected_diff_section_empty}\n{Reviewer.PROMPT}"

    actual_prompt_empty = reviewer_instance._make_files_prompt(diffs_empty)
    assert actual_prompt_empty == expected_prompt_empty

    # --- Test case 3: Single diff file ---
    diffs_single = [df1]
    # Context for a single file: context = "" (initial) + "" (initial) + context_df1_str
    expected_context_single = context_df1_str
    expected_diff_section_single = f"<DIFF>\n{df1.diff}\n</DIFF>"
    expected_prompt_single = f"{expected_context_single}\n{expected_diff_section_single}\n{Reviewer.PROMPT}"

    actual_prompt_single = reviewer_instance._make_files_prompt(diffs_single)
    assert actual_prompt_single == expected_prompt_single
