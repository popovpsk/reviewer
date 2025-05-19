import logging
import re
from dataclasses import dataclass

from reviewer.llm.llm import LLM
from reviewer.system_utils import os
from reviewer.system_utils.diff import DiffFile
from reviewer.agents.go_tools import list_go_package_files
from reviewer.system_utils.os import get_file_content

REQUIRED_DATA_FROM_OTHER_PACKAGES_PROMPT = """You are to conduct a code review.
I provided you with the modified file and its original version from the master branch.
You must not conduct the review right now. Write down which additional code from the project you will have to perform a higher-quality review.
Request only the minimal but truly necessary imports. You already know infrastructure-related things and standard library.
List the fully qualified import statements for the classes and functions you would like to see.
As a result, only output the code without ''' and nothing else.
Output only the imports with the class or specific function name you want, in the strict format `packet:name1,name2`, where `packet` is the full name of the module with path, and `name1,name2` is the class, function, method, variable, etc... definitions of this packet.
If you want method and class, separate this name, for example import_path:MyClass,NewMyClass,MyClass.Do 
Besides this list, there should be no other words in your response."""

REQUIRED_DATA_FROM_THIS_PACKAGE_PROMPT = """You are to conduct a code review. I provided you with the modified file and its original version from the master branch.
You must not conduct the review right now. Write down which additional code from this package you will need to perform a higher-quality review. 
Request only the minimal but truly necessary code. You already know infrastructure-related things and the standard library.
Output only the list of names: classes, functions, methods, variables, etc.
Request data only from this package. Data from other packages will be requested separately.
As a result, only output the code without ''' and nothing else.
Besides this list, there should be no other words in your response.
I will use this list to request this code to augment future prompts.
If you dont need additional context from this package write only CONTEXT_NOT_FOUND.
"""

FIND_DEFINITION_IN_PACKAGE_PROMPT = """I provided you with a list of files from the package. 
Find the definition of: {} in it and output only that code.
As a result, only output the code without ''' and nothing else.
You are not allowed to output anything except that definition. 
You are strictly forbidden from inventing code yourself. You may only return results based on the code I provided.
If the definition is missing, write only CONTEXT_NOT_FOUND."""


@dataclass
class ImportDefinition:
    import_path: str
    definition: str


# Регулярное выражение для разбора строки формата "packet:name"
imports_pattern = re.compile(
    r"^(?P<import_path>[\w./-]+):(?P<definition>\w+)$", re.MULTILINE
)


class ContextRetriever:
    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def retrieve_context(self, file: DiffFile) -> None:
        logging.debug(f"seek_context: {file.name}")
        additional_context: list[str] = []
        from_this_package = self.retrieve_from_this_package(file)
        if from_this_package:
            additional_context.extend(from_this_package)

        additional_context.extend(self.retrieve_from_other_packages(file))
        file.additional_context = additional_context

    def retrieve_from_other_packages(self, file: DiffFile) -> list[str]:
        additional_context: list[str] = []
        prompt = f"\ndiff:\n{file.diff}\n original file from master:\n {file.original_content}\n{REQUIRED_DATA_FROM_OTHER_PACKAGES_PROMPT}"
        result = self.llm.generate(f"retrieve from other packages{file.name}", prompt)
        requests = self.parse_imports(result)
        for context_request in requests:
            context = self.find_definition(context_request)
            if context:
                additional_context.append(context)
        return additional_context

    def retrieve_from_this_package(self, file: DiffFile) -> list[str]:
        logging.debug(f"retrieve_from_this_package: {file.name}")
        prompt = f"\ndiff:\n{file.diff},\noriginal file from master:\n {file.original_content}\n{REQUIRED_DATA_FROM_THIS_PACKAGE_PROMPT} "
        requested_context = self.llm.generate(
            f"retrieve_from_this_package {file.name}", prompt
        )
        if "CONTEXT_NOT_FOUND" in requested_context:
            return []

        result: list[str] = []
        files = os.find_other_files_in_directory(file.full_name)
        for path in files:
            prompt = f"{os.get_file_content(path)}\n{FIND_DEFINITION_IN_PACKAGE_PROMPT.format(requested_context)}"
            context = self.llm.generate(f"find context in {file.name}", prompt)
            if "CONTEXT_NOT_FOUND" not in context:
                result.append(context)

        return result

    @staticmethod
    def parse_imports(input_text: str) -> list[ImportDefinition]:

        results = []
        for match in imports_pattern.finditer(input_text):
            import_path = match.group("import_path")
            definition = match.group("definition")
            results.append(
                ImportDefinition(import_path=import_path, definition=definition)
            )

        return results

    def find_definition(self, definition: ImportDefinition) -> str:
        prompt = FIND_DEFINITION_IN_PACKAGE_PROMPT.format(definition.definition)
        file_paths = list_go_package_files(definition.import_path)

        files = ""
        for path in file_paths:
            if not path.is_file():
                continue

            file_content = get_file_content(str(path))
            files += f"\nfile:{path.name}\ncontent:\n{file_content}"

        prompt = files + prompt

        result = self.llm.generate(
            f"find in other imports:{definition.definition}", prompt
        )
        if "CONTEXT_NOT_FOUND" in result:
            return ""
        return result
