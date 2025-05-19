import os
import subprocess
from pathlib import Path

env = os.environ.copy()
env["PATH"] += ":/usr/local/go/bin"  # Добавь путь, если его нет


def list_go_package_files(package: str) -> list[Path]:
    try:
        # Получаем путь к директории пакета
        result = subprocess.run(
            ["go", "list", "-f", "{{.Dir}}", package],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        package_dir = Path(result.stdout.strip())
        if not package_dir.exists() or not package_dir.is_dir():
            raise RuntimeError(
                f"Directory {package_dir} does not exist or is not a directory."
            )

        return list(package_dir.iterdir())
    except subprocess.CalledProcessError as e:
        return []
