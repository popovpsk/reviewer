import os
from pathlib import Path
from typing import Dict, Optional, Any
from tree_sitter import Parser, Language, Tree
from tree_sitter_languages import get_language

class AstParser:
    """
    Parses files in a repository into Abstract Syntax Trees (ASTs)
    using tree-sitter. Supports Python, Go, and TypeScript.
    """
    def __init__(self, repo_path: str):
        """
        Initializes the AstParser with the path to the repository.

        Args:
            repo_path: The root path of the code repository.
        """
        self.repo_path: Path = Path(repo_path)
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")

        self.parser: Parser = Parser()
        self._language_map: Dict[str, str] = {
            ".py": "python",
            ".go": "go",
            ".ts": "typescript",
            ".tsx": "tsx",  # TypeScript with JSX
        }
        # Eagerly load languages to catch issues early
        try:
            self._tree_sitter_languages: Dict[str, Language] = {
                "python": get_language("python"),
                "go": get_language("go"),
                "typescript": get_language("typescript"),
                "tsx": get_language("tsx"),
            }
        except Exception as e:
            # This can happen if the grammars are not correctly installed/found
            raise RuntimeError(
                "Failed to load tree-sitter languages. "
                "Ensure tree-sitter grammars are correctly installed. "
                f"Original error: {e}"
            )


    def _get_tree_sitter_language(self, file_path: Path) -> Language | None:
        """
        Determines the tree-sitter Language object based on the file extension.
        """
        suffix: str = file_path.suffix.lower() # Use lower for case-insensitivity
        lang_name: Optional[str] = self._language_map.get(suffix)
        if lang_name:
            return self._tree_sitter_languages.get(lang_name)
        return None

    def parse_file_to_ast(self, file_path: Path) -> Optional[Tree]:
        """
        Parses a single file and returns its tree-sitter AST (Tree object).

        Args:
            file_path: The absolute or relative path to the file.

        Returns:
            A tree_sitter.Tree object if parsing is successful, None otherwise.
        """
        absolute_file_path: Path = file_path
        if not absolute_file_path.is_absolute():
            absolute_file_path = self.repo_path / file_path

        if not absolute_file_path.is_file():
            print(f"Warning: File not found: {absolute_file_path}")
            return None

        language = self._get_tree_sitter_language(absolute_file_path)
        if not language:
            # This file type is not supported, skip silently or log as debug
            # print(f"Debug: Unsupported language for file: {absolute_file_path}")
            return None

        self.parser.set_language(language)

        try:
            with open(absolute_file_path, "rb") as f:  # tree-sitter expects bytes
                content: bytes = f.read()
            tree: Tree = self.parser.parse(content)
            return tree
        except Exception as e:
            print(f"Error parsing file {absolute_file_path}: {e}")
            return None

    def generate_repomap(self) -> Dict[str, Any]:
        """
        Generates a representation of the repository structure and code elements.
        This is a placeholder and should be expanded to extract meaningful
        information from ASTs for LLM consumption.
        """
        repomap_data: Dict[str, Any] = {}
        print(f"Starting repomap generation for repository: {self.repo_path}")

        for file_path in self.repo_path.rglob("*"):  # Iterate through all files recursively
            if file_path.is_file():
                # Check if the file extension is in our supported languages
                if file_path.suffix.lower() in self._language_map:
                    # print(f"Attempting to parse: {file_path.relative_to(self.repo_path)}")
                    ast: Optional[Tree] = self.parse_file_to_ast(file_path)
                    if ast:
                        # Placeholder: In a real scenario, extract relevant info from AST
                        # For example, function names, class names, imports, etc.
                        repomap_data[str(file_path.relative_to(self.repo_path))] = {
                            "status": "AST_parsed_successfully",
                            "node_count": len(ast.root_node.children) # Example metric
                        }
                    else:
                         repomap_data[str(file_path.relative_to(self.repo_path))] = {
                            "status": "AST_parsing_failed_or_skipped"
                        }
                # else:
                    # print(f"Skipping unsupported file type: {file_path.relative_to(self.repo_path)}")
        
        print("Repomap generation (placeholder) complete.")
        # For debugging, you might want to print parts of the repomap_data
        # For example, print the first 5 entries:
        # for i, (k, v) in enumerate(repomap_data.items()):
        #     if i < 5:
        #         print(f"  {k}: {v}")
        #     else:
        #         break
        return repomap_data
