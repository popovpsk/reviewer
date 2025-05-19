import os


def get_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        raise e


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path) and os.path.isfile(file_path)


def basename(file_path: str) -> str:
    return os.path.basename(file_path)


def find_other_files_in_directory(path: str) -> list[str]:
    directory = os.path.dirname(path)
    exclude_file = os.path.basename(path)

    result: list[str] = []
    for filename in os.listdir(directory):
        if filename != exclude_file:
            full_path = os.path.join(directory, filename)
            if os.path.isfile(full_path):
                result.append(full_path)

    return result


def clear_directory(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                clear_directory(file_path)
                os.rmdir(file_path)
        except Exception as e:
            print(f"Ошибка при удалении {file_path}: {e}")
