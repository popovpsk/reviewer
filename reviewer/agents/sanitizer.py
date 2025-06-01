import logging

from reviewer.ast_parser.ast_parser import ASTParser
from reviewer.llm.llm import LLM
from reviewer.system_utils.diff import DiffFile


SANITIZE_PROMPT = """
Instructions:
You are provided with the following:
1.  The content of an original source code file (hereinafter referred to as "the Original File").
2.  A diff. This diff represents the changes made to the Original File (and potentially other related files) to create a new version.
Your goal is to identify code definitions (e.g., functions, classes, methods, significant standalone code blocks) present in the Original File that are not meaningful for the purpose of a subsequent code review aimed at assessing the quality, correctness, and impact of the primary changes.
Crucial Consideration: If any definition, even if it seems like boilerplate or a utility, *contains or is the primary site of significant algorithmic or logical changes* introduced by the diff, it IS meaningful and SHOULD NOT be listed. The focus is on excluding code that is noise relative to the core changes.
Output Requirements:
*   You MUST list only the identifiers (names) of these code definitions deemed not meaningful for code review.
*   Each identifier MUST be on a new line.
*   There MUST be no other symbols, text, explanations, or formatting (like bullet points or numbering) in your output.
*   Your entire output MUST consist ONLY of these identifiers, each on its own line.
Example:
```python
@my_decorator
def func_to_remove(a):
    pass

def func_to_keep():
    print("hello")

class ClassToRemove:
    def method(self):
        pass

class ClassToKeep:
    pass

dict_to_remove = {"a": 1, "b": 2}
dict_to_keep = {"c": 3}
```
answer:
func_to_remove
ClassToRemove
dict_to_remove
"""

CONTEXT = """
<file_name>{}</file_name>
<original_file_content>
{}
</original_file_content>
<diff>
{}
</diff>
"""


class Sanitizer:
    def __init__(self, llm: LLM, ast_parser: ASTParser) -> None:
        self.__llm = llm
        self.__ast_parser = ast_parser

    def sanitize(self, file: DiffFile, diffs: list[DiffFile]) -> None:
        logging.debug(f"sanitize source: {file.name}")

        original_file = self.__ast_parser.parse(
            file.full_name, bytes(file.original_content, "utf-8")
        )
        if not original_file:
            return

        git_diff = "\n".join([d.diff for d in diffs])

        prompt = (
                CONTEXT.format(file.full_name, file.original_content, git_diff)
                + SANITIZE_PROMPT
        )

        llm_response = self.__llm.generate(f"sanitize:{file.name}", prompt)
        declarations_to_delete = self.__parse_llm_response(llm_response)
        if not declarations_to_delete:
            return

        for definition in declarations_to_delete:
            original_file.remove_declaration(definition)

        file.original_content = original_file.content.decode("utf-8")

    @staticmethod
    def __parse_llm_response(response: str) -> list[str]:
        if not response:
            return []

        lines = response.splitlines()

        identifiers = [line.strip() for line in lines if line.strip()]

        return identifiers
