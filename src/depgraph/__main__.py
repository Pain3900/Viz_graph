"""Точка входа: ``python -m depgraph --package ИМЯ --repo URL``."""

import sys

from depgraph import registry, repo_file
from depgraph.config import PROGRAM_NAME, ConfigError, parse_config
from depgraph.graph import build_graph

CONFIG_ERROR_CODE = 2
DATA_ERROR_CODE = 1


def file_source(path, root):
    """Вернуть функцию получения зависимостей из тестового файла.

    Корневой пакет обязан быть в файле; зависимость, не описанная
    отдельной строкой, считается пакетом без зависимостей.
    """
    packages = repo_file.load_repo(path)
    repo_file.direct_dependencies(packages, root)
    return lambda name: packages.get(name, [])


def registry_source(url, labels):
    """Вернуть функцию получения зависимостей из реестра npm.

    Версия каждого пакета записывается в ``labels`` как ``имя@версия``.
    """
    def get_dependencies(name):
        version, dependencies = registry.direct_dependencies(url, name)
        labels[name] = f"{name}@{version}"
        return sorted(dependencies)
    return get_dependencies


def collect_graph(args):
    """Построить граф; вернуть (граф, циклы, подписи пакетов)."""
    labels = {}
    if args.test_mode:
        source = file_source(args.repo, args.package)
    else:
        source = registry_source(args.repo, labels)
    graph, cycles = build_graph(args.package, source, args.filter)
    return graph, cycles, labels


def format_graph(graph, cycles, labels):
    """Оформить граф списком смежности и строками циклов."""
    root = next(iter(graph))
    lines = [f"Dependency graph of {labels.get(root, root)} "
             f"(packages: {len(graph)}):"]
    for name, dependencies in graph.items():
        targets = ", ".join(dependencies) or "(none)"
        lines.append(f"  {labels.get(name, name)} -> {targets}")
    for cycle in cycles:
        lines.append("Cycle: " + " -> ".join(cycle))
    return lines


def report_error(exc, code):
    """Вывести ошибку в stderr и вернуть код завершения."""
    print(f"{PROGRAM_NAME}: error: {exc}", file=sys.stderr)
    return code


def main(argv=None):
    """Разобрать параметры, построить и вывести граф зависимостей."""
    try:
        args = parse_config(argv)
    except ConfigError as exc:
        return report_error(exc, CONFIG_ERROR_CODE)
    try:
        graph, cycles, labels = collect_graph(args)
    except (registry.RegistryError, repo_file.RepoFileError) as exc:
        return report_error(exc, DATA_ERROR_CODE)
    for line in format_graph(graph, cycles, labels):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
