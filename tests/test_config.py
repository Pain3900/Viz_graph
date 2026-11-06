"""Тесты разбора и проверки параметров командной строки."""

import contextlib
import io
import os
import unittest

from depgraph.config import ConfigError, format_config, parse_config

URL = "https://registry.npmjs.org"
TEST_REPO = os.path.join(os.path.dirname(__file__), "..", "repos",
                         "simple.txt")


def parse_error(argv):
    """Разобрать параметры и вернуть текст ошибки ConfigError."""
    try:
        parse_config(argv)
    except ConfigError as exc:
        return str(exc)
    raise AssertionError(f"no ConfigError for {argv}")


def argparse_fails(argv):
    """Проверить, что argparse отклоняет параметры (SystemExit)."""
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            parse_config(argv)
        except SystemExit:
            return True
    return False


class ValidConfigTest(unittest.TestCase):
    """Корректные наборы параметров."""

    def test_real_mode_defaults(self):
        """Обязательные опции и значения по умолчанию."""
        args = parse_config(["--package", "react", "--repo", URL])
        self.assertEqual(format_config(args), [
            "package=react", f"repo={URL}", "test_mode=false",
            "ascii_tree=false", "filter=(not set)"])

    def test_all_options(self):
        """Все опции заданы."""
        args = parse_config(["--package", "@types/node", "--repo", URL,
                             "--ascii-tree", "--filter", "test"])
        self.assertEqual(format_config(args), [
            "package=@types/node", f"repo={URL}", "test_mode=false",
            "ascii_tree=true", "filter=test"])

    def test_test_mode(self):
        """Тестовый режим: имя из больших букв и путь к файлу."""
        args = parse_config(["--package", "A", "--repo", TEST_REPO,
                             "--test-mode"])
        self.assertTrue(args.test_mode)
        self.assertIn("test_mode=true", format_config(args))

    def test_npm_names(self):
        """Допустимые имена npm: точки, дефисы, области видимости."""
        for name in ("lodash.merge", "left-pad", "@babel/core", "a"):
            parse_config(["--package", name, "--repo", URL])


class PackageErrorTest(unittest.TestCase):
    """Ошибки параметра --package."""

    def test_missing(self):
        """Без --package argparse завершает работу."""
        self.assertTrue(argparse_fails(["--repo", URL]))

    def test_empty(self):
        """Пустое имя."""
        self.assertIn("must not be empty",
                      parse_error(["--package", "", "--repo", URL]))

    def test_uppercase(self):
        """В обычном режиме имя только из маленьких букв."""
        self.assertIn("lowercase",
                      parse_error(["--package", "React", "--repo", URL]))

    def test_invalid_characters(self):
        """Недопустимые символы и начало с точки."""
        for name in (".hidden", "my package", "a/b", "@/x"):
            self.assertIn("invalid npm package name",
                          parse_error(["--package", name, "--repo", URL]))

    def test_too_long(self):
        """Имя длиннее 214 символов."""
        self.assertIn("longer than 214",
                      parse_error(["--package", "a" * 215, "--repo", URL]))

    def test_test_mode_name(self):
        """В тестовом режиме имя только из больших латинских букв."""
        for name in ("a", "A1", "Б"):
            self.assertIn("capital Latin letters", parse_error(
                ["--package", name, "--repo", TEST_REPO, "--test-mode"]))


class RepoErrorTest(unittest.TestCase):
    """Ошибки параметра --repo."""

    def test_missing(self):
        """Без --repo argparse завершает работу."""
        self.assertTrue(argparse_fails(["--package", "react"]))

    def test_empty(self):
        """Пустое значение."""
        self.assertIn("must not be empty",
                      parse_error(["--package", "react", "--repo", ""]))

    def test_bad_url(self):
        """Не URL или не http(s)."""
        for url in ("registry.npmjs.org", "ftp://x.org", "https://"):
            self.assertIn("expected http:// or https:// URL",
                          parse_error(["--package", "react", "--repo", url]))

    def test_test_file_missing(self):
        """В тестовом режиме файла нет."""
        self.assertIn("file not found", parse_error(
            ["--package", "A", "--repo", "nope.txt", "--test-mode"]))

    def test_test_file_is_directory(self):
        """В тестовом режиме указан каталог."""
        directory = os.path.dirname(TEST_REPO)
        self.assertIn("not a file", parse_error(
            ["--package", "A", "--repo", directory, "--test-mode"]))


class FlagAndFilterErrorTest(unittest.TestCase):
    """Ошибки флагов и параметра --filter."""

    def test_flags_take_no_value(self):
        """Флаги не принимают значений."""
        for flag in ("--test-mode=yes", "--ascii-tree=1"):
            self.assertTrue(argparse_fails(
                ["--package", "react", "--repo", URL, flag]))

    def test_unknown_option(self):
        """Неизвестная опция."""
        self.assertTrue(argparse_fails(
            ["--package", "react", "--repo", URL, "--depth", "2"]))

    def test_filter_empty(self):
        """Пустая подстрока фильтра."""
        self.assertIn("must not be empty", parse_error(
            ["--package", "react", "--repo", URL, "--filter", ""]))

    def test_filter_spaces(self):
        """Подстрока фильтра с пробелами."""
        self.assertIn("must not contain spaces", parse_error(
            ["--package", "react", "--repo", URL, "--filter", "a b"]))

    def test_filter_without_value(self):
        """--filter без значения."""
        self.assertTrue(argparse_fails(
            ["--package", "react", "--repo", URL, "--filter"]))


class ReverseTest(unittest.TestCase):
    """Флаг --reverse."""

    def test_test_mode(self):
        """В тестовом режиме флаг допустим."""
        args = parse_config(["--package", "A", "--repo", TEST_REPO,
                             "--test-mode", "--reverse"])
        self.assertTrue(args.reverse)

    def test_registry_mode(self):
        """Для реестра npm обратные зависимости не поддерживаются."""
        self.assertEqual(parse_error(
            ["--package", "ms", "--repo", URL, "--reverse"]),
            "--reverse: works only with --test-mode")


if __name__ == "__main__":
    unittest.main()
