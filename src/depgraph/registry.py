"""Получение прямых зависимостей пакета из реестра npm.

Используется только стандартная библиотека (urllib). Запрашиваются
сокращённые метаданные пакета (формат ``install-v1``): в них нет README
и описаний версий, поэтому ответ в десятки раз меньше полного.
"""

import json
import urllib.error
import urllib.request
from urllib.parse import quote

ABBREVIATED_METADATA = "application/vnd.npm.install-v1+json"
TIMEOUT_SECONDS = 15
HTTP_NOT_FOUND = 404


class RegistryError(Exception):
    """Не удалось получить или разобрать данные из реестра."""


def package_url(repo, name):
    """Вернуть URL метаданных пакета.

    В имени ``@scope/имя`` косая черта кодируется как ``%2F``.
    """
    return f"{repo.rstrip('/')}/{quote(name, safe='@')}"


def fetch_metadata(repo, name):
    """Загрузить метаданные пакета и вернуть их как словарь."""
    url = package_url(repo, name)
    request = urllib.request.Request(
        url, headers={"Accept": ABBREVIATED_METADATA})
    try:
        with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code == HTTP_NOT_FOUND:
            raise RegistryError(f"package not found: '{name}'") from exc
        raise RegistryError(
            f"HTTP error {exc.code} {exc.reason} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RegistryError(
            f"cannot connect to {repo}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RegistryError(f"timed out while reading {url}") from exc
    try:
        return json.loads(body)
    except ValueError as exc:
        raise RegistryError(f"invalid JSON in response from {url}") from exc


def latest_dependencies(metadata, name):
    """Вернуть (версия, зависимости) для версии ``latest``.

    Зависимости - поле ``dependencies`` выбранной версии: словарь
    ``имя -> диапазон версий``. dev-, peer- и optional-зависимости
    не учитываются.
    """
    if not isinstance(metadata, dict):
        raise RegistryError(f"unexpected metadata format for '{name}'")
    version = (metadata.get("dist-tags") or {}).get("latest")
    if not version:
        raise RegistryError(f"no 'latest' version for '{name}'")
    manifest = (metadata.get("versions") or {}).get(version)
    if not isinstance(manifest, dict):
        raise RegistryError(
            f"version {version} of '{name}' is missing in metadata")
    dependencies = manifest.get("dependencies") or {}
    if not isinstance(dependencies, dict):
        raise RegistryError(
            f"invalid 'dependencies' in {name}@{version}")
    return version, dependencies


def direct_dependencies(repo, name):
    """Получить из реестра (версия, прямые зависимости) пакета."""
    metadata = fetch_metadata(repo, name)
    return latest_dependencies(metadata, name)
