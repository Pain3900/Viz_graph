"""Тесты точки входа: вывод параметров и коды завершения."""

import contextlib
import io
import unittest

from depgraph.__main__ import main


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

    def test_prints_key_value(self):
        """Параметры выводятся в формате ключ=значение."""
        code, out, err = self.run_main(
            ["--package", "react", "--repo", "https://registry.npmjs.org",
             "--filter", "test"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, "package=react\n"
                              "repo=https://registry.npmjs.org\n"
                              "test_mode=false\nascii_tree=false\n"
                              "filter=test\n")

    def test_error_code_and_message(self):
        """Ошибка значения: сообщение в stderr и код 2."""
        code, out, err = self.run_main(
            ["--package", "React", "--repo", "https://x.org"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, "depgraph: error: --package: name must be "
                              "lowercase: 'React'\n")


if __name__ == "__main__":
    unittest.main()
