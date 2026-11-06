"""Параметры командной строки и их проверка.

Все настраиваемые пользователем параметры задаются опциями командной
строки. Разбор выполняет модуль argparse, а проверку значений -
функция :func:`validate`, которая сообщает о первой найденной ошибке.
"""

import argparse
import os
import re
from urllib.parse import urlparse

PROGRAM_NAME = "depgraph"
MAX_NAME_LENGTH = 214
URL_SCHEMES = ("http", "https")
NOT_SET = "(not set)"
NPM_NAME_PATTERN = re.compile(
    r"^(@[a-z0-9~-][a-z0-9._~-]*/)?[a-z0-9~-][a-z0-9._~-]*$")
TEST_NAME_PATTERN = re.compile(r"^[A-Z]+$")


class ConfigError(Exception):
    """Ошибка в значении параметра командной строки."""


def build_parser():
    """Создать разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Визуализация графа зависимостей npm-пакетов.")
    parser.add_argument(
        "--package", required=True,
        help="имя анализируемого пакета")
    parser.add_argument(
        "--repo", required=True,
        help="URL репозитория или путь к файлу тестового репозитория")
    parser.add_argument(
        "--test-mode", action="store_true",
        help="работать с тестовым репозиторием из файла")
    parser.add_argument(
        "--ascii-tree", action="store_true",
        help="выводить зависимости в виде ASCII-дерева")
    parser.add_argument(
        "--filter", default=None,
        help="не учитывать пакеты, имя которых содержит подстроку")
    parser.add_argument(
        "--reverse", action="store_true",
        help="вывести обратные зависимости (только с --test-mode)")
    return parser


def check_package(name, test_mode):
    """Проверить имя пакета по правилам npm или тестового режима."""
    if not name:
        raise ConfigError("--package: name must not be empty")
    if test_mode:
        if not TEST_NAME_PATTERN.match(name):
            raise ConfigError(
                f"--package: in test mode name must consist of capital "
                f"Latin letters: '{name}'")
        return
    if len(name) > MAX_NAME_LENGTH:
        raise ConfigError(
            f"--package: name is longer than {MAX_NAME_LENGTH} characters")
    if name != name.lower():
        raise ConfigError(f"--package: name must be lowercase: '{name}'")
    if not NPM_NAME_PATTERN.match(name):
        raise ConfigError(f"--package: invalid npm package name: '{name}'")


def check_url(url):
    """Проверить, что URL начинается с http(s) и содержит сервер."""
    parsed = urlparse(url)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"--repo: expected http:// or https:// URL, got '{url}'")


def check_test_file(path):
    """Проверить, что путь ведёт к существующему файлу."""
    if not os.path.exists(path):
        raise ConfigError(f"--repo: file not found: '{path}'")
    if not os.path.isfile(path):
        raise ConfigError(f"--repo: not a file: '{path}'")


def check_filter(substring):
    """Проверить подстроку фильтра: непустая и без пробелов."""
    if substring is None:
        return
    if not substring:
        raise ConfigError("--filter: substring must not be empty")
    if any(char.isspace() for char in substring):
        raise ConfigError(
            f"--filter: substring must not contain spaces: '{substring}'")


def validate(args):
    """Проверить значения всех параметров.

    Raises:
        ConfigError: при первой найденной ошибке.
    """
    check_package(args.package, args.test_mode)
    if not args.repo:
        raise ConfigError("--repo: value must not be empty")
    if args.test_mode:
        check_test_file(args.repo)
    else:
        check_url(args.repo)
    check_filter(args.filter)
    if args.reverse and not args.test_mode:
        raise ConfigError("--reverse: works only with --test-mode")


def parse_config(argv=None):
    """Разобрать и проверить параметры; вернуть argparse.Namespace.

    Ошибки формата (нет обязательной опции, лишнее значение у флага)
    обрабатывает argparse, ошибки значений - :func:`validate`.
    """
    args = build_parser().parse_args(argv)
    validate(args)
    return args


def format_config(args):
    """Вернуть параметры в виде строк ``ключ=значение``."""
    values = {
        "package": args.package,
        "repo": args.repo,
        "test_mode": args.test_mode,
        "ascii_tree": args.ascii_tree,
        "filter": args.filter,
    }
    lines = []
    for key, value in values.items():
        if value is None:
            value = NOT_SET
        elif isinstance(value, bool):
            value = str(value).lower()
        lines.append(f"{key}={value}")
    return lines
