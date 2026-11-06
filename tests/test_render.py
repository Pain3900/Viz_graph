"""Тесты визуализации: Mermaid, ASCII-дерево, изображение."""

import base64
import io
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from depgraph.render import (MERMAID_INK_URL, RenderError, ascii_tree,
                             image_url, save_image, to_mermaid)

URLOPEN = "urllib.request.urlopen"
DIAMOND = {"A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]}
CYCLE = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}


class MermaidTest(unittest.TestCase):
    """Текст графа на языке Mermaid."""

    def test_diamond(self):
        """Узлы с подписями, затем рёбра."""
        self.assertEqual(to_mermaid(DIAMOND, {}), [
            "graph TD",
            '    n1["A"]', '    n2["B"]', '    n3["D"]', '    n4["C"]',
            "    n1 --> n2", "    n1 --> n4",
            "    n2 --> n3", "    n4 --> n3"])

    def test_labels_with_versions(self):
        """Имена npm с @ и / идут в подписи, не в идентификаторы."""
        graph = {"@babel/core": ["ms"], "ms": []}
        labels = {"@babel/core": "@babel/core@7.0.0", "ms": "ms@2.1.3"}
        self.assertEqual(to_mermaid(graph, labels)[1:], [
            '    n1["@babel/core@7.0.0"]', '    n2["ms@2.1.3"]',
            "    n1 --> n2"])

    def test_cycle_edge_kept(self):
        """Ребро цикла остаётся в графе."""
        self.assertIn("    n3 --> n1", to_mermaid(CYCLE, {}))


class AsciiTreeTest(unittest.TestCase):
    """ASCII-дерево зависимостей."""

    def test_diamond(self):
        """Пакет без зависимостей повторяется без пометки."""
        self.assertEqual(ascii_tree(DIAMOND, "A", {}), [
            "A", "├── B", "│   └── D", "└── C", "    └── D"])

    def test_see_above(self):
        """Уже показанный пакет с зависимостями не раскрывается."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["B"], "D": []}
        self.assertEqual(ascii_tree(graph, "A", {}), [
            "A", "├── B", "│   └── D", "└── C", "    └── B (see above)"])

    def test_cycle(self):
        """Ребро цикла помечается (cycle)."""
        self.assertEqual(ascii_tree(CYCLE, "A", {}), [
            "A", "└── B", "    └── C", "        ├── A (cycle)",
            "        └── D"])

    def test_labels(self):
        """Пакеты подписаны версиями."""
        labels = {"debug": "debug@4.4.3", "ms": "ms@2.1.3"}
        self.assertEqual(ascii_tree({"debug": ["ms"], "ms": []},
                                    "debug", labels),
                         ["debug@4.4.3", "└── ms@2.1.3"])


class ImageTest(unittest.TestCase):
    """Сохранение изображения через mermaid.ink (без сети)."""

    def setUp(self):
        """Временная папка для файла изображения."""
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "graph.svg")

    def tearDown(self):
        """Удалить временную папку."""
        self.folder.cleanup()

    def test_url(self):
        """В адресе - текст Mermaid в base64."""
        url = image_url(["graph TD", "    n1 --> n2"])
        self.assertTrue(url.startswith(MERMAID_INK_URL))
        encoded = url[len(MERMAID_INK_URL):]
        self.assertEqual(base64.urlsafe_b64decode(encoded),
                         b"graph TD\n    n1 --> n2")

    def test_saved(self):
        """Ответ сервиса записывается в файл."""
        with mock.patch(URLOPEN, return_value=io.BytesIO(b"<svg/>")):
            save_image(["graph TD"], self.path)
        with open(self.path, "rb") as image_file:
            self.assertEqual(image_file.read(), b"<svg/>")

    def assert_error(self, text, path=None, **patch_args):
        """Проверить, что RenderError содержит текст."""
        with mock.patch(URLOPEN, **patch_args):
            with self.assertRaises(RenderError) as context:
                save_image(["graph TD"], path or self.path)
        self.assertIn(text, str(context.exception))

    def test_http_error(self):
        """Сервис ответил ошибкой."""
        error = urllib.error.HTTPError("u", 503, "Unavailable", None, None)
        self.assert_error("HTTP error 503", side_effect=error)

    def test_no_connection(self):
        """Сервис недоступен."""
        self.assert_error("cannot render image: no route", side_effect=(
            urllib.error.URLError("no route")))

    def test_timeout(self):
        """Истекло время ожидания."""
        self.assert_error("timed out", side_effect=TimeoutError())

    def test_write_error(self):
        """Файл нельзя записать (путь - папка)."""
        self.assert_error("cannot write", path=self.folder.name,
                          return_value=io.BytesIO(b"<svg/>"))


if __name__ == "__main__":
    unittest.main()
