"""Точка входа: ``python -m depgraph --package ИМЯ --repo URL``."""

import sys

from depgraph import registry, repo_file
from depgraph.config import PROGRAM_NAME, ConfigError, parse_config

CONFIG_ERROR_CODE = 2
DATA_ERROR_CODE = 1


def collect_dependencies(args):
    """Вернуть (заголовок, строки) с прямыми зависимостями пакета."""
    if args.test_mode:
        packages = repo_file.load_repo(args.repo)
        names = repo_file.direct_dependencies(packages, args.package)
        return args.package, names
    version, dependencies = registry.direct_dependencies(
        args.repo, args.package)
    lines = [f"{name} {spec}"
             for name, spec in sorted(dependencies.items())]
    return f"{args.package}@{version}", lines


def format_dependencies(title, lines):
    """Оформить список прямых зависимостей для вывода."""
    result = [f"Direct dependencies of {title}:"]
    result += [f"  {line}" for line in lines] or ["  (none)"]
    return result


def report_error(exc, code):
    """Вывести ошибку в stderr и вернуть код завершения."""
    print(f"{PROGRAM_NAME}: error: {exc}", file=sys.stderr)
    return code


def main(argv=None):
    """Разобрать параметры, вывести прямые зависимости пакета."""
    try:
        args = parse_config(argv)
    except ConfigError as exc:
        return report_error(exc, CONFIG_ERROR_CODE)
    try:
        title, lines = collect_dependencies(args)
    except (registry.RegistryError, repo_file.RepoFileError) as exc:
        return report_error(exc, DATA_ERROR_CODE)
    for line in format_dependencies(title, lines):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
