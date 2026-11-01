"""Тесты точки входа: вывод прямых зависимостей и коды завершения."""

import contextlib
import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from depgraph.__main__ import main

URL = "https://registry.npmjs.org"
REPOS = os.path.join(os.path.dirname(__file__), "..", "repos")
SIMPLE = os.path.join(REPOS, "simple.txt")
EXPRESS = {
    "name": "express",
    "dist-tags": {"latest": "5.1.0"},
    "versions": {"5.1.0": {"dependencies": {
        "accepts": "^2.0.0", "body-parser": "^2.2.0"}}},
}


class MainTest(unittest.TestCase):
    """Проверки функции main."""

    def run_main(self, argv):
        """Запустить main и вернуть (код, вывод, ошибки)."""
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_registry_dependencies(self):
        """Прямые зависимости из реестра с диапазонами версий."""
        body = io.BytesIO(json.dumps(EXPRESS).encode("utf-8"))
        with mock.patch("urllib.request.urlopen", return_value=body):
            code, out, err = self.run_main(
                ["--package", "express", "--repo", URL])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Direct dependencies of express@5.1.0:\n"
                              "  accepts ^2.0.0\n"
                              "  body-parser ^2.2.0\n")

    def test_test_mode_dependencies(self):
        """Прямые зависимости из тестового файла."""
        code, out, _ = self.run_main(
            ["--package", "A", "--repo", SIMPLE, "--test-mode"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "Direct dependencies of A:\n  B\n  C\n")

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        _, out, _ = self.run_main(
            ["--package", "D", "--repo", SIMPLE, "--test-mode"])
        self.assertEqual(out, "Direct dependencies of D:\n  (none)\n")

    def test_registry_error_code(self):
        """Пакет не найден в реестре: сообщение в stderr и код 1."""
        error = urllib.error.HTTPError(URL, 404, "Not Found", None, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            code, out, err = self.run_main(
                ["--package", "no-such-pkg", "--repo", URL])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, "depgraph: error: package not found: "
                              "'no-such-pkg'\n")

    def test_repo_file_error_code(self):
        """Ошибка формата тестового файла: код 1."""
        code, _, err = self.run_main(
            ["--package", "A", "--repo", os.path.join(REPOS, "broken.txt"),
             "--test-mode"])
        self.assertEqual(code, 1)
        self.assertIn("expected 'NAME: DEPENDENCIES'", err)

    def test_config_error_code(self):
        """Ошибка значения параметра: сообщение в stderr и код 2."""
        code, out, err = self.run_main(
            ["--package", "React", "--repo", "https://x.org"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, "depgraph: error: --package: name must be "
                              "lowercase: 'React'\n")


if __name__ == "__main__":
    unittest.main()
