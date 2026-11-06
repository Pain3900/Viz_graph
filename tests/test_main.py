"""Тесты точки входа: порядок загрузки, граф и коды завершения."""

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
REGISTRY = {
    "debug": ("4.4.3", {"ms": "^2.1.3"}),
    "ms": ("2.1.3", {}),
}


def fake_urlopen(request, timeout):
    """Ответ реестра по имени пакета в конце URL."""
    name = request.full_url.rsplit("/", 1)[1]
    if name not in REGISTRY:
        raise urllib.error.HTTPError(URL, 404, "Not Found", None, None)
    version, dependencies = REGISTRY[name]
    document = {"dist-tags": {"latest": version},
                "versions": {version: {"dependencies": dependencies}}}
    return io.BytesIO(json.dumps(document).encode("utf-8"))


class MainTest(unittest.TestCase):
    """Проверки функции main."""

    def run_main(self, argv):
        """Запустить main и вернуть (код, вывод, ошибки)."""
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err), \
                mock.patch("urllib.request.urlopen", fake_urlopen):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def run_file(self, package, file_name, *options):
        """Запустить в тестовом режиме с файлом из repos/."""
        return self.run_main(
            ["--package", package, "--repo",
             os.path.join(REPOS, file_name), "--test-mode", *options])

    def test_registry_mermaid(self):
        """Реестр: порядок загрузки и Mermaid, пакеты с версиями."""
        code, out, err = self.run_main(["--package", "debug", "--repo", URL])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Load order of debug@4.4.3:\n"
                              "  1. ms@2.1.3\n"
                              "  2. debug@4.4.3\n"
                              "\n"
                              "graph TD\n"
                              '    n1["debug@4.4.3"]\n'
                              '    n2["ms@2.1.3"]\n'
                              "    n1 --> n2\n")

    def test_simple_file(self):
        """Тестовый файл: Mermaid по умолчанию."""
        code, out, _ = self.run_file("A", "simple.txt")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("Load order of A:\n"
                                       "  1. D\n  2. B\n  3. C\n"
                                       "  4. A\n\ngraph TD\n"))

    def test_cycle_ascii_tree(self):
        """Цикл и ASCII-дерево вместо Mermaid."""
        _, out, _ = self.run_file("A", "cycle.txt", "--ascii-tree")
        self.assertEqual(out, "Load order of A:\n"
                              "  1. D\n  2. C\n  3. B\n  4. A\n"
                              "Cycle: A -> B -> C -> A\n"
                              "\n"
                              "A\n"
                              "└── B\n"
                              "    └── C\n"
                              "        ├── A (cycle)\n"
                              "        └── D\n")

    def test_filter_file(self):
        """Фильтр исключает пакеты с подстрокой."""
        _, out, _ = self.run_file("APP", "filter.txt", "--filter", "TEST",
                                  "--ascii-tree")
        self.assertEqual(out, "Load order of APP:\n"
                              "  1. CORE\n  2. LIB\n  3. APP\n"
                              "\nAPP\n└── LIB\n    └── CORE\n")

    def test_image_error_code(self):
        """Не удалось получить изображение: код 1."""
        code, _, err = self.run_file("A", "simple.txt", "--image",
                                     os.path.join(REPOS, "..", "x.svg"))
        self.assertEqual(code, 1)
        self.assertIn("cannot render image", err)

    def test_reverse(self):
        """Обратные зависимости: кто зависит от D напрямую и через других."""
        _, out, _ = self.run_file("D", "simple.txt", "--reverse")
        self.assertEqual(out, "Reverse dependencies of D (dependents: 3):\n"
                              "  D <- B, C\n  B <- A\n"
                              "  A <- (none)\n  C <- A\n")

    def test_reverse_cycle_and_filter(self):
        """Цикл и фильтр работают и для обратных зависимостей."""
        _, out, _ = self.run_file("A", "cycle.txt", "--reverse")
        self.assertTrue(out.endswith("Cycle: A <- C <- B <- A\n"))
        _, out, _ = self.run_file("CORE", "filter.txt", "--reverse",
                                  "--filter", "TEST")
        self.assertEqual(out, "Reverse dependencies of CORE "
                              "(dependents: 2):\n"
                              "  CORE <- LIB\n  LIB <- APP\n"
                              "  APP <- (none)\n")

    def test_registry_error_code(self):
        """Пакет не найден в реестре: сообщение в stderr и код 1."""
        code, out, err = self.run_main(
            ["--package", "no-such-pkg", "--repo", URL])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, "depgraph: error: package not found: "
                              "'no-such-pkg'\n")

    def test_root_missing_in_file(self):
        """Корневого пакета нет в тестовом файле: код 1."""
        code, _, err = self.run_file("Z", "simple.txt")
        self.assertEqual(code, 1)
        self.assertIn("package not found in test repository: 'Z'", err)

    def test_repo_file_error_code(self):
        """Ошибка формата тестового файла: код 1."""
        code, _, err = self.run_file("A", "broken.txt")
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
