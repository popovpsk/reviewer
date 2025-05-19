import logging
import os
from collections import defaultdict

from reviewer.agents.review import Reviewer
from reviewer.agents.sanitizer import Sanitizer
from reviewer.config.reviewer_config import Configuration
from reviewer.system_utils.diff import DiffFile
from reviewer.tokenizator.token_counter import TokenCounter

class ReviewModes:
    def __init__(self, config: Configuration, reviewer: Reviewer, token_counter: TokenCounter, sanitizer: Sanitizer):
        self.__config = config
        self.__reviewer = reviewer
        self.__token_counter = token_counter
        self.__sanitizer = sanitizer


    def auto(self, diffs: list[DiffFile]) -> list[str]:
        for diff in diffs:
            diff.tokens_count = self.__token_counter.count_tokens(diff.original_content + diff.diff)
            if diff.tokens_count < 2048:
                continue

            diff.original_content = self.__sanitizer.sanitize(diff)
            diff.tokens_count = self.__token_counter.count_tokens(diff.original_content + diff.diff)

        if sum(diff.tokens_count for diff in diffs) < self.__config.context_window:
            return self.all_files_at_once(diffs)

        groups = self.split_by_context_recursive(diffs)
        result = []
        for group in groups:
            result.append(self.__reviewer.review_files(group))

        return result

    def split_by_context_recursive(self, diffs: list[DiffFile]) -> list[list[DiffFile]]:
        """
        Splits a list of DiffFile objects into sublists (groups) based on token counts
        and a context window limit.

        The method tries to keep files from the same directory together if the entire
        directory fits within the context window. If a directory is too large, its files
        are split and processed individually (sorted by name).

        Items (whole small directories or individual files from large directories) are
        packed greedily into groups, prioritizing smaller items to maximize the number
        of files within each group under the context window limit.
        """
        if not diffs:
            return []

        grouped_by_directory = self.__group_by_directory(diffs)
        limit = self.__config.context_window
        packable_items = []

        type_map = {'dir': 0, 'file': 1, 'file_oversized': 2}

        # Create packable items from directories
        sorted_directory_paths = sorted(grouped_by_directory.keys())

        for directory_path in sorted_directory_paths:
            dir_files = grouped_by_directory[directory_path]
            dir_total_tokens = sum(f.tokens_count for f in dir_files)

            if dir_total_tokens == 0:
                continue

            if dir_total_tokens <= limit:
                # This directory as a whole can be a packable item
                packable_items.append({
                    'id': directory_path,
                    'files': list(dir_files), # Keep original order of files within small dir
                    'tokens': dir_total_tokens,
                    'type': 'dir',
                    'original_path': directory_path
                })
            else:
                # Directory is too large, break it into individual files
                sorted_files_in_dir = sorted(dir_files, key=lambda f: f.name)
                for file_obj in sorted_files_in_dir:
                    if file_obj.tokens_count == 0:
                        continue
                    
                    item_type = 'file_oversized' if file_obj.tokens_count > limit else 'file'
                    packable_items.append({
                        'id': file_obj.full_name,
                        'files': [file_obj],
                        'tokens': file_obj.tokens_count,
                        'type': item_type,
                        'original_path': file_obj.full_name
                    })

        # Sort packable items: by tokens, then type (dirs first), then path
        packable_items.sort(key=lambda x: (x['tokens'], type_map[x['type']], x['original_path']))

        all_groups: list[list[DiffFile]] = []
        current_group_files: list[DiffFile] = []
        current_group_tokens = 0

        for item in packable_items:
            item_files = item['files']
            item_tokens = item['tokens']

            if item['type'] == 'file_oversized':
                if current_group_files:
                    all_groups.append(list(current_group_files))
                    current_group_files = []
                    current_group_tokens = 0
                all_groups.append(list(item_files)) # Oversized item forms its own group
                continue

            # item_tokens is guaranteed to be <= limit here (unless it's an oversized dir that wasn't split, which logic prevents)
            if current_group_tokens + item_tokens <= limit:
                current_group_files.extend(item_files)
                current_group_tokens += item_tokens
            else:
                if current_group_files:
                    all_groups.append(list(current_group_files))
                current_group_files = list(item_files)
                current_group_tokens = item_tokens
        
        if current_group_files:
            all_groups.append(list(current_group_files))

        return all_groups

    def file_by_file(self, diffs: list[DiffFile]) -> list[str]:
        result = []
        for diff_file in diffs:
            review = self.__reviewer.review_file(diff_file)
            result.append(result)
        return result

    def all_files_at_once(self, diffs: list[DiffFile]) -> list[str]:
        if diffs:
            review = self.__reviewer.review_files(diffs)
            return [review]
        else:
            logging.info("No files to review in AllFilesAtOnce mode.")
            return []

    def package_by_package(self, diffs: list[DiffFile]) -> list[str]:
        result = []
        grouped_by_directory = self.__group_by_directory(diffs)
        for directory, files_in_dir in grouped_by_directory.items():
            if files_in_dir:
                review = self.__reviewer.review_files(files_in_dir, directory)
                result.append(review)
            else:
                logging.info(f"No files to review in package: {directory}")

        return result

    @staticmethod
    def __group_by_directory(objects: list[DiffFile]) -> dict[str, list[DiffFile]]:
        grouped_by_directory = defaultdict(list)

        for obj in objects:
            full_path = obj.full_name
            directory = os.path.dirname(full_path)
            grouped_by_directory[directory].append(obj)

        return grouped_by_directory
