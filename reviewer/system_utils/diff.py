from dataclasses import dataclass, field

from . import git, os


@dataclass
class DiffFile:
    name: str
    diff: str
    full_name: str
    original_content: str = ""
    additional_context: list[str] = field(default_factory=list)
    tokens_count: int = 0


def diff_master(branch: str):
    git.fetch()
    git.pull()
    git.checkout(branch)

    branches = git.get_local_branches()
    if branch not in branches:
        raise ValueError("branch does not exist")

    git.checkout(branch)
    git.pull()

    git.checkout("master")


def get_git_diff_files(base_branch: str, target_branch: str) -> list[DiffFile]:
    changed_files = git.get_changed_files(base_branch, target_branch)
    diff_files: list[DiffFile] = []

    for changed_file in changed_files:
        if os.file_exists(changed_file):
            full_content = os.get_file_content(changed_file)
            file_diff = git.get_file_diff(base_branch, target_branch, changed_file)

            # Создаем Diff и добавляем его в список
            diff_files.append(
                DiffFile(
                    name=os.basename(changed_file),
                    original_content=full_content,
                    diff=file_diff,
                    full_name=changed_file,
                )
            )
        else:
            file_diff = git.get_file_diff(base_branch, target_branch, changed_file)
            diff_files.append(
                DiffFile(
                    name=os.basename(changed_file),
                    diff=file_diff,
                    full_name=changed_file,
                )
            )

    return diff_files
