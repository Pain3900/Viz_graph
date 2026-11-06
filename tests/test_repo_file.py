"""Тесты чтения тестового репозитория из файла."""

import os
import unittest

from depgraph.repo_file import (RepoFileError, direct_dependencies,
                                load_repo, parse_repo,
                                reverse_dependencies)

REPOS = os.path.join(os.path.dirname(__file__), "..", "repos")


def parse_error(lines):
    """Разобрать строки и вернуть текст ошибки RepoFileError."""
    try:
        parse_repo(lines, "repo.txt")
    except RepoFileError as exc:
        return str(exc)
    raise AssertionError(f"no RepoFileError for {lines}")


class ParseRepoTest(unittest.TestCase):
    """Корректные файлы."""

    def test_simple_file(self):
        """Файл repos/simple.txt."""
        packages = load_repo(os.path.join(REPOS, "simple.txt"))
        self.assertEqual(packages, {"A": ["B", "C"], "B": ["D"],
                                    "C": ["D"], "D": []})

    def test_spaces_and_empty_lines(self):
        """Лишние пробелы и пустые строки не мешают."""
        packages = parse_repo(["  A :B   C\n", "\n", "B:\n"], "repo.txt")
        self.assertEqual(packages, {"A": ["B", "C"], "B": []})

    def test_direct_dependencies(self):
        """Прямые зависимости пакета."""
        packages = {"A": ["B", "C"], "B": []}
        self.assertEqual(direct_dependencies(packages, "A"), ["B", "C"])
        self.assertEqual(direct_dependencies(packages, "B"), [])

    def test_reverse_dependencies(self):
        """Обратные зависимости: кто зависит от пакета."""
        packages = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(reverse_dependencies(packages),
                         {"B": ["A"], "C": ["A"], "D": ["B", "C"]})


class RepoFileErrorTest(unittest.TestCase):
    """Ошибки формата файла."""

    def test_no_colon(self):
        """Строка без двоеточия; в сообщении номер строки."""
        self.assertEqual(parse_error(["A: B\n", "B C\n"]),
                         "repo.txt:2: expected 'NAME: DEPENDENCIES'")

    def test_invalid_names(self):
        """Имена пакета и зависимостей только из больших букв."""
        self.assertIn("invalid package name 'a'", parse_error(["a: B"]))
        self.assertIn("invalid package name 'B1'", parse_error(["A: B1"]))
        self.assertIn("invalid package name ''", parse_error([": B"]))

    def test_defined_twice(self):
        """Пакет описан дважды."""
        self.assertIn("package 'A' is defined twice",
                      parse_error(["A: B", "B:", "A: C"]))

    def test_package_not_found(self):
        """Пакета нет в репозитории."""
        with self.assertRaises(RepoFileError) as context:
            direct_dependencies({"A": []}, "Z")
        self.assertIn("package not found in test repository: 'Z'",
                      str(context.exception))


if __name__ == "__main__":
    unittest.main()
