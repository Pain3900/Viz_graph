"""Тесты получения зависимостей из реестра npm (без сети)."""

import io
import json
import unittest
import urllib.error
from unittest import mock

from depgraph.registry import (ABBREVIATED_METADATA, RegistryError,
                               direct_dependencies, package_url)

URL = "https://registry.npmjs.org"
URLOPEN = "urllib.request.urlopen"


def metadata(version="1.0.0", dependencies=None):
    """Сокращённые метаданные пакета с одной версией."""
    manifest = {"name": "pkg", "version": version}
    if dependencies is not None:
        manifest["dependencies"] = dependencies
    return {"name": "pkg", "dist-tags": {"latest": version},
            "versions": {version: manifest}}


def response(document):
    """Ответ сервера с JSON-документом."""
    return io.BytesIO(json.dumps(document).encode("utf-8"))


def http_error(code, reason):
    """Исключение HTTPError с заданным кодом."""
    return urllib.error.HTTPError(URL, code, reason, None, None)


class PackageUrlTest(unittest.TestCase):
    """Построение URL метаданных."""

    def test_plain_name(self):
        """Обычное имя добавляется к адресу реестра."""
        self.assertEqual(package_url(URL, "express"), f"{URL}/express")

    def test_scoped_name(self):
        """В имени с областью видимости '/' кодируется."""
        self.assertEqual(package_url(URL + "/", "@babel/core"),
                         f"{URL}/@babel%2Fcore")


class DirectDependenciesTest(unittest.TestCase):
    """Разбор ответа реестра."""

    def test_dependencies_of_latest(self):
        """Берутся dependencies версии latest, остальное не нужно."""
        document = metadata("2.0.0", {"a": "^1.0.0", "b": "~2.1.0"})
        document["versions"]["2.0.0"]["devDependencies"] = {"c": "1"}
        document["versions"]["1.0.0"] = {"dependencies": {"old": "1"}}
        with mock.patch(URLOPEN, return_value=response(document)) as urlopen:
            version, dependencies = direct_dependencies(URL, "pkg")
        self.assertEqual(version, "2.0.0")
        self.assertEqual(dependencies, {"a": "^1.0.0", "b": "~2.1.0"})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, f"{URL}/pkg")
        self.assertEqual(request.get_header("Accept"), ABBREVIATED_METADATA)

    def test_no_dependencies(self):
        """У версии нет поля dependencies."""
        with mock.patch(URLOPEN, return_value=response(metadata())):
            self.assertEqual(direct_dependencies(URL, "pkg"), ("1.0.0", {}))


class RegistryErrorTest(unittest.TestCase):
    """Ошибки сети и формата данных."""

    def assert_error(self, text, **patch_args):
        """Проверить, что RegistryError содержит текст."""
        with mock.patch(URLOPEN, **patch_args):
            with self.assertRaises(RegistryError) as context:
                direct_dependencies(URL, "pkg")
        self.assertIn(text, str(context.exception))

    def test_not_found(self):
        """HTTP 404 - пакета нет в реестре."""
        self.assert_error("package not found: 'pkg'",
                          side_effect=http_error(404, "Not Found"))

    def test_other_http_error(self):
        """Другие коды HTTP."""
        self.assert_error("HTTP error 500",
                          side_effect=http_error(500, "Server Error"))

    def test_no_connection(self):
        """Сервер недоступен."""
        self.assert_error("cannot connect to", side_effect=(
            urllib.error.URLError("nodename nor servname provided")))

    def test_timeout(self):
        """Истекло время ожидания."""
        self.assert_error("timed out", side_effect=TimeoutError())

    def test_invalid_json(self):
        """Ответ не JSON."""
        self.assert_error("invalid JSON",
                          return_value=io.BytesIO(b"<html></html>"))

    def test_no_latest(self):
        """Нет dist-tags.latest."""
        self.assert_error("no 'latest' version",
                          return_value=response({"versions": {}}))

    def test_latest_missing_in_versions(self):
        """Версия latest не описана в versions."""
        document = metadata("1.0.0")
        document["dist-tags"]["latest"] = "9.9.9"
        self.assert_error("version 9.9.9 of 'pkg' is missing",
                          return_value=response(document))

    def test_not_object(self):
        """Ответ - JSON, но не объект."""
        self.assert_error("unexpected metadata format",
                          return_value=response([1, 2]))


if __name__ == "__main__":
    unittest.main()
