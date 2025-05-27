import unittest
from unittest.mock import Mock

from reviewer.system_utils.diff import DiffFile
from reviewer.config.reviewer_config import Configuration
from reviewer.processor.review_modes import ReviewModes


class TestSplitByContextRecursive(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock(spec=Configuration)
        self.mock_reviewer = Mock()
        self.mock_token_counter = Mock()
        self.mock_sanitizer = Mock()
        self.review_modes = ReviewModes(
            config=self.mock_config,
            reviewer=self.mock_reviewer,
            token_counter=self.mock_token_counter,
            sanitizer=self.mock_sanitizer,
        )

    @staticmethod
    def _create_diff_file(full_name: str, tokens: int) -> DiffFile:
        parts = full_name.split("/")
        name = parts[-1]
        return DiffFile(
            name=name,
            full_name=full_name,
            diff="",
            original_content="",
            tokens_count=tokens,
        )

    @staticmethod
    def _get_file_names(groups: list[list[DiffFile]]) -> list[list[str]]:
        return [[df.full_name for df in group] for group in groups]

    def test_empty_diffs(self):
        self.mock_config.context_window = 8000
        diffs = []
        result = self.review_modes.split_by_context_recursive(diffs)
        self.assertEqual(result, [])

    def test_all_fit_in_one_group(self):
        self.mock_config.context_window = 8000
        diffs = [
            self._create_diff_file("dir1/file1.py", 1000),
            self._create_diff_file("dir1/file2.py", 1500),
            self._create_diff_file("dir2/file3.py", 2000),
        ]
        # dir1: 2500, dir2: 2000. Total 4500.
        # Packable items (sorted by tokens, type, path):
        # dir2 (2000), dir1 (2500)
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [["dir2/file3.py", "dir1/file1.py", "dir1/file2.py"]]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_multiple_small_dirs_forming_groups(self):
        self.mock_config.context_window = 8000
        # Dirs: A(3k), B(3k), C(3k), D(3k)
        diffs = [
            self._create_diff_file("dir_a/file1.py", 3000),
            self._create_diff_file("dir_b/file2.py", 3000),
            self._create_diff_file("dir_c/file3.py", 3000),
            self._create_diff_file("dir_d/file4.py", 3000),
        ]
        # Packable items: dir_a(3k), dir_b(3k), dir_c(3k), dir_d(3k) (sorted by path)
        # Group1: dir_a, dir_b (6k)
        # Group2: dir_c, dir_d (6k)
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [
            ["dir_a/file1.py", "dir_b/file2.py"],
            ["dir_c/file3.py", "dir_d/file4.py"],
        ]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_mix_small_and_large_dirs(self):
        self.mock_config.context_window = 8000
        # Dirs: A(2k), B(15k -> B1(5k), B2(5k), B3(5k)), C(7k), D(2k)
        diffs = [
            self._create_diff_file("dir_a/file_a.py", 2000),  # Dir A
            self._create_diff_file("dir_b/file_b1.py", 5000),  # Dir B
            self._create_diff_file("dir_b/file_b2.py", 5000),  # Dir B
            self._create_diff_file("dir_b/file_b3.py", 5000),  # Dir B
            self._create_diff_file("dir_c/file_c.py", 7000),  # Dir C
            self._create_diff_file("dir_d/file_d.py", 2000),  # Dir D
        ]
        # Packable items sorted by (tokens, type, path):
        # 1. dir_a (2000, dir, "dir_a/file_a.py")
        # 2. dir_d (2000, dir, "dir_d/file_d.py")
        # 3. dir_b/file_b1.py (5000, file, "dir_b/file_b1.py")
        # 4. dir_b/file_b2.py (5000, file, "dir_b/file_b2.py")
        # 5. dir_b/file_b3.py (5000, file, "dir_b/file_b3.py")
        # 6. dir_c (7000, dir, "dir_c/file_c.py")

        # Packing:
        # Group1: dir_a (2k) + dir_d (2k) = 4k.  Remaining 4k.
        #         dir_b/file_b1.py (5k) doesn't fit.
        # Group2: dir_b/file_b1.py (5k). Remaining 3k.
        #         dir_b/file_b2.py (5k) doesn't fit.
        # Group3: dir_b/file_b2.py (5k). Remaining 3k.
        #         dir_b/file_b3.py (5k) doesn't fit.
        # Group4: dir_b/file_b3.py (5k). Remaining 3k.
        #         dir_c (7k) doesn't fit.
        # Group5: dir_c (7k).
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [
            ["dir_a/file_a.py", "dir_d/file_d.py"],  # Group 1 (4k)
            ["dir_b/file_b1.py"],  # Group 2 (5k)
            ["dir_b/file_b2.py"],  # Group 3 (5k)
            ["dir_b/file_b3.py"],  # Group 4 (5k)
            ["dir_c/file_c.py"],  # Group 5 (7k)
        ]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_single_large_dir_split_into_files(self):
        self.mock_config.context_window = 8000
        diffs = [
            self._create_diff_file(
                "large_dir/file_c.py", 3000
            ),  # ensure sorted by name
            self._create_diff_file("large_dir/file_a.py", 4000),
            self._create_diff_file("large_dir/file_b.py", 5000),
        ]  # Total 12000 for large_dir.
        # Files from large_dir, sorted by name: file_a (4k), file_b (5k), file_c (3k)
        # Packable items: file_c(3k), file_a(4k), file_b(5k) (sorted by tokens, then path)
        # 1. file_c (3k)
        # 2. file_a (4k)
        # 3. file_b (5k)
        # Packing:
        # Group1: file_c (3k) + file_a (4k) = 7k.
        # Group2: file_b (5k)
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [
            [
                "large_dir/file_c.py",
                "large_dir/file_a.py",
            ],  # files are sorted by name when dir is split, then packed by token size
            ["large_dir/file_b.py"],
        ]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_file_oversized(self):
        self.mock_config.context_window = 8000
        diffs = [
            self._create_diff_file("dir1/small_file.py", 1000),
            self._create_diff_file("dir2/oversized_file.py", 9000),
            self._create_diff_file("dir3/another_small.py", 1500),
        ]
        # Packable items (sorted):
        # 1. dir1/small_file (1k, dir)
        # 2. dir3/another_small (1.5k, dir)
        # 3. dir2/oversized_file (9k, file_oversized)
        # Packing:
        # Group1: dir1/small_file (1k) + dir3/another_small (1.5k) = 2.5k
        # Oversized file dir2/oversized_file (9k) is handled next.
        # Group2: dir2/oversized_file (9k)
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [
            ["dir1/small_file.py", "dir3/another_small.py"],
            ["dir2/oversized_file.py"],
        ]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_files_with_zero_tokens(self):
        self.mock_config.context_window = 8000
        diffs = [
            self._create_diff_file("dir1/file1.py", 1000),
            self._create_diff_file("dir1/zero_token_file.py", 0),
            self._create_diff_file("dir2/file2.py", 2000),
        ]
        # dir1: 1000, dir2: 2000. Zero token file is ignored for packing items.
        # Packable items: dir1 (1k), dir2 (2k)
        # Group1: dir1 (file1.py only) + dir2 (file2.py) = 3k
        result = self.review_modes.split_by_context_recursive(diffs)
        # The zero token file is part of dir1 if dir1 is packed as a whole.
        expected_names = [["dir1/file1.py", "dir1/zero_token_file.py", "dir2/file2.py"]]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_files_with_zero_tokens_in_large_dir(self):
        self.mock_config.context_window = 3000
        diffs = [
            self._create_diff_file("large_dir/file1.py", 2000),
            self._create_diff_file("large_dir/zero_file.py", 0),
            self._create_diff_file("large_dir/file2.py", 2500),
        ]  # large_dir total 4500.
        # Files from large_dir (sorted): file1(2k), file2(2.5k), zero_file(0k)
        # Packable items: file1(2k), file2(2.5k). zero_file is skipped.
        # Group1: file1(2k)
        # Group2: file2(2.5k)
        result = self.review_modes.split_by_context_recursive(diffs)
        expected_names = [
            ["large_dir/file1.py"],
            ["large_dir/file2.py"],
        ]
        self.assertEqual(self._get_file_names(result), expected_names)

    def test_order_of_files_in_small_dir_preserved(self):
        self.mock_config.context_window = 8000
        diffs = [
            self._create_diff_file("dir1/file_z.py", 100),
            self._create_diff_file("dir1/file_a.py", 100),
        ]  # dir1 total 200
        result = self.review_modes.split_by_context_recursive(diffs)
        # Files within a small directory that is packed as a whole should maintain their original relative order.
        expected_names = [["dir1/file_z.py", "dir1/file_a.py"]]
        self.assertEqual(self._get_file_names(result), expected_names)


if __name__ == "__main__":
    unittest.main()
