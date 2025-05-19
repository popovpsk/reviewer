import logging

from reviewer.llm.llm import LLM
from reviewer.system_utils.diff import DiffFile


SANITIZE_PROMPT = """Original file:\n{}\n//source file code ends here\ngit-diff:\n{}\nI gave you original file and diff from this file to new version.
You will perform a code review
To make it more precisely, you need to reduce the future input context. 
Output the edited original file in which the code that is not necessary for reviewing the changes is removed.
If you think a specific definition in the code is necessary and will be needed during the future review, keep it.
You are not allowed to modify the remaining code, only delete the code that is unnecessary for the code review.
Remove comments.
Please provide me result with the Go code in plain text format"""


class Sanitizer:
    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def sanitize(self, diff: DiffFile) -> str:
        logging.debug(f"sanitize source: {diff.name}")

        prompt = SANITIZE_PROMPT.format(diff.original_content, diff.diff)
        return self.llm.generate(f"sanitize:{diff.name}", prompt)
