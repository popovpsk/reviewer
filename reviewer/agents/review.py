import logging
from typing import List

from reviewer.llm.llm import LLM
from reviewer.system_utils.diff import DiffFile


class Reviewer:
    PROMPT = """Instructions:
You need to perform code review.
Point out poor practices or needed improvements.
Highlight any obvious bugs or mistakes.
Review only the code in the diff block, but use all context i gave you if you need it.
If you have a comment, please specify the file name.
If the code is correct and contains no errors, reply only: no comments.
Do not mention the lack of comments or documentation.
Do not be overly critical of naming choices.
Do not explain the code.
All this code has already been compiled successfully and has no compilation and linting errors.
Tests have been compiled and passed, but the project lacks 100% coverage, offering no guarantees.
Keep your feedback direct and concise.
Focus exclusively on significant issues and errors.
Respond without using any Markdown formatting, code blocks, or special highlighting—just plain text.
Begin your review now."""

    CONTEXT = """<file_name>
{}
</file_name>
<master_version>
```{}
{}
```
</master_version>>
<diff>
```git diff
{}
```
</diff>\n"""

    def __init__(self, llm: LLM):
        self.llm = llm

    def review_file(self, diff: DiffFile) -> str:
        logging.debug(f"review file: {diff.name}")

        context = self.CONTEXT.format(
            diff.full_name,
            self.__language_from_extension(diff.name),
            diff.original_content,
            diff.diff,
        )
        prompt = f"{context}{self.PROMPT}"

        result = self.llm.generate(f"review: {diff.name}", prompt)
        formatted = f"\n{diff.name}:{result}"
        return formatted

    def review_files(self, diffs: List[DiffFile], name: str = "all files") -> str:
        context = ""
        for f in diffs:
            context = context + self.CONTEXT.format(
                f.full_name,
                self.__language_from_extension(f.name),
                f.original_content,
                f.diff,
            )

        prompt = f"{context}{self.PROMPT}"
        result = self.llm.generate(f"review: {name}", prompt)
        formatted = f"\n{name}:{result}"
        return formatted

    @staticmethod
    def __language_from_extension(file_name: str) -> str:
        extension = file_name.split(".")[-1]
        return {
            "py": "python",
            "go": "go",
            "proto": "proto",
            "js": "javascript",
            "ts": "javascript",
        }.get(extension, extension)
