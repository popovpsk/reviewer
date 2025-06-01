import os
import subprocess


def get_local_branches() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "branch", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        branches = result.stdout.splitlines()
        branches = [branch.strip("* ").strip() for branch in branches]
        return branches

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
        return []


def fetch() -> None:
    run_git_command(["fetch"])


def pull() -> None:
    run_git_command(["pull", "origin"])


def checkout(branch: str) -> None:
    run_git_command(["checkout", branch])


def get_changed_files(base_branch: str, target_branch: str) -> list[str]:
    command = ["diff", "--name-only", f"{base_branch}...{target_branch}"]
    result = run_git_command(command)
    return result.splitlines() if result else []


def get_file_diff(base_branch: str, target_branch: str, file_path: str) -> str:
    """Получает git diff для указанного файла между двумя ветками."""
    command = ["diff", f"{base_branch}...{target_branch}", "--", file_path]
    return run_git_command(command)


def run_git_command(command: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + command,
            capture_output=True,
            text=True,
            check=True,
            env=os.environ.copy(),
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: git {command} : {e.stderr}")
        raise e
