"""Тестовый репозиторий: пакеты и зависимости из текстового файла.

Формат файла - по одному пакету в строке::

    A: B C
    B: D
    D:

Слева от двоеточия имя пакета, справа - его прямые зависимости через
пробел. Имена состоят из больших латинских букв. Пустые строки
пропускаются.
"""

from depgraph.config import TEST_NAME_PATTERN


class RepoFileError(Exception):
    """Ошибка в файле тестового репозитория."""


def check_name(name, path, line_number):
    """Проверить, что имя пакета состоит из больших латинских букв."""
    if not TEST_NAME_PATTERN.match(name):
        raise RepoFileError(
            f"{path}:{line_number}: invalid package name '{name}'")


def parse_repo(lines, path):
    """Разобрать строки файла; вернуть словарь ``имя -> [зависимости]``."""
    packages = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        if ":" not in line:
            raise RepoFileError(
                f"{path}:{line_number}: expected 'NAME: DEPENDENCIES'")
        name, _, rest = line.partition(":")
        name = name.strip()
        check_name(name, path, line_number)
        if name in packages:
            raise RepoFileError(
                f"{path}:{line_number}: package '{name}' "
                f"is defined twice")
        dependencies = rest.split()
        for dependency in dependencies:
            check_name(dependency, path, line_number)
        packages[name] = dependencies
    return packages


def load_repo(path):
    """Прочитать файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as repo_file:
            return parse_repo(repo_file, path)
    except (OSError, UnicodeDecodeError) as exc:
        raise RepoFileError(f"cannot read '{path}': {exc}") from exc


def direct_dependencies(packages, name):
    """Вернуть прямые зависимости пакета из тестового репозитория."""
    if name not in packages:
        raise RepoFileError(
            f"package not found in test repository: '{name}'")
    return packages[name]
