import logging
from typing import Optional

from grep_ast import filename_to_lang
from grep_ast.tsl import get_language, get_parser
from tree_sitter import Node, Tree
from tree_sitter_languages.core import Language

# Define query patterns for identifying declarations.
# These are for Python. More languages can be added.
_PYTHON_DECLARATION_QUERIES = [
    # Query for decorated functions/classes (captures the whole decorated block)
    (
        """
        (decorated_definition
          definition: [
            (function_definition name: (identifier) @name (#eq? @name "{0}"))
            (class_definition name: (identifier) @name (#eq? @name "{0}"))
          ]
        ) @declaration
        """,
        "declaration",  # Capture name for the node to remove
    ),
    # Query for non-decorated functions
    (
        """
        (function_definition
          name: (identifier) @name (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for non-decorated classes
    (
        """
        (class_definition
          name: (identifier) @name (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for assignment statements
    (
        """
        (expression_statement
            (assignment
                left: (identifier) @name (#eq? @name "{0}")
            )
        ) @declaration
        """,
        "declaration",
    ),
]

# Define query patterns for Go
_GO_DECLARATION_QUERIES = [
    # Query for functions
    (
        """
        (function_declaration
          name: (identifier) @name (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for methods
    (
        """
        (method_declaration
          name: (field_identifier) @name (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for type specifications (e.g., structs, interfaces)
    # This targets the individual type spec, e.g., `MyType int` in `type ( MyType int )`
    (
        """
        (type_declaration
            (type_spec
                name: (type_identifier) @name
            )
            (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for constant specifications
    # This targets the individual const spec, e.g., `MyConst = 1` in `const ( MyConst = 1 )`
    (
        """
        (const_spec
          name: (identifier) @name (#eq? @name "{}")
        ) @declaration
        """,
        "declaration",
    ),
    # Query for short variable declarations (e.g., var := value)
    (
        """
        (short_var_declaration
          left: (expression_list (identifier) @name (#eq? @name "{0}"))
        ) @declaration
        """,
        "declaration",
    ),
    # Query for var specifications (e.g. var myVar = 1 or var myVar int = 1)
    # This targets the var_spec itself.
    (
        """
        (var_declaration
            (var_spec
                name: (identifier) @name
            )
            (#eq? @name "{0}")
        ) @declaration
        """,
        "declaration",
    ),
    ## Query for blocks of var declarations
    (
        """
        (var_spec
          name: (identifier) @name (#eq? @name "{0}")
        ) @declaration
        """,
        "declaration",
    ),
]

# Define query patterns for Protocol Buffers
_PROTO_DECLARATION_QUERIES = [
    # Query for messages
    (
        """
        (message
          (message_name
            (identifier) @name (#eq? @name "{}")
          ) 
        ) @declaration
        """,
        "declaration",
    ),
    # Query for rpc calls within a service
    (
        """
        (rpc
          (rpc_name
            (identifier) @name (#eq? @name "{}")
          ) 
        ) @declaration
        """,
        "declaration",
    ),
]

_LANG_SPECIFIC_QUERIES = {
    "python": _PYTHON_DECLARATION_QUERIES,
    "go": _GO_DECLARATION_QUERIES,
    "proto": _PROTO_DECLARATION_QUERIES,
    # Add queries for other languages here, e.g., "javascript"
}


class ParsedFile:
    def __init__(self, tree: Tree, original_content: bytes, lang: str):
        self.tree = tree
        self.original_content = original_content
        self.content = original_content
        self.lang = lang
        self.language: Language = get_language(lang)

    def remove_declaration(self, name_to_remove: str) -> bool:
        """Removes a class or function/method declaration by its name.
        Updates self.content and re-parses self.tree.
        Returns True if a declaration was found and removed, False otherwise.
        """
        query_patterns = _LANG_SPECIFIC_QUERIES.get(self.lang)
        if not query_patterns:
            return False  # No queries defined for this language

        node_to_remove_data: Optional[tuple[int, int]] = None  # Stores (start_byte, end_byte) of the node

        for query_text_template, _capture_name_for_node in query_patterns:
            formatted_query_text = query_text_template.format(name_to_remove)
            try:
                query = self.language.query(formatted_query_text)
            except Exception as e:  # Syntax error in query, or other tree-sitter issue
                logging.log(logging.ERROR, f"Failed to query {formatted_query_text} due to {e}")
                continue

            captures: dict[str, list[Node]] = query.captures(self.tree.root_node)

            if len(captures) == 0:
                continue

            name = captures["name"][0].text
            if name == bytes(name_to_remove, "utf-8"):
                node = captures["declaration"][0]
                node_to_remove_data = (node.start_byte, node.end_byte)
                break

        if node_to_remove_data:
            start_byte, end_byte = node_to_remove_data

            # Remove the content of the node
            self.content = self.content[:start_byte] + self.content[end_byte:]

            # Re-parse the modified content
            parser = get_parser(self.lang)
            self.tree = parser.parse(self.content)
            return True

        return False


class ASTParser:
    def __init__(self):
        pass

    def parse(self, path_to_file: str, content: bytes) -> Optional[ParsedFile]:
        lang = filename_to_lang(path_to_file)
        if not lang or lang not in _LANG_SPECIFIC_QUERIES:
            return None

        if lang is None:
            raise ValueError(f"Could not determine language for file: {path_to_file}")

        tree = self.__file_to_tree(lang, content)
        return ParsedFile(tree=tree, original_content=content, lang=lang)

    @staticmethod
    def __file_to_tree(lang: str, content: bytes) -> Tree:
        parser = get_parser(lang)
        tree = parser.parse(content)
        return tree
