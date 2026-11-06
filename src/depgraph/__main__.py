"""Точка входа: ``python -m depgraph --package ИМЯ --repo URL``."""

import sys

from depgraph import registry, render, repo_file
from depgraph.config import PROGRAM_NAME, ConfigError, parse_config
from depgraph.graph import build_graph, load_order

CONFIG_ERROR_CODE = 2
DATA_ERROR_CODE = 1
DATA_ERRORS = (registry.RegistryError, repo_file.RepoFileError,
               render.RenderError)


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


def format_load_order(graph, cycles, labels):
    """Оформить порядок загрузки и найденные циклы."""
    root = next(iter(graph))
    lines = [f"Load order of {labels.get(root, root)}:"]
    for number, name in enumerate(load_order(graph, root), start=1):
        lines.append(f"  {number}. {labels.get(name, name)}")
    for cycle in cycles:
        lines.append("Cycle: " + " -> ".join(cycle))
    return lines


def visualize(args, graph, labels):
    """Вывести граф (Mermaid или ASCII-дерево), сохранить изображение."""
    mermaid = render.to_mermaid(graph, labels)
    if args.ascii_tree:
        lines = render.ascii_tree(graph, args.package, labels)
    else:
        lines = mermaid
    print()
    for line in lines:
        print(line)
    if args.image:
        render.save_image(mermaid, args.image)


def report_error(exc, code):
    """Вывести ошибку в stderr и вернуть код завершения."""
    print(f"{PROGRAM_NAME}: error: {exc}", file=sys.stderr)
    return code


def main(argv=None):
    """Разобрать параметры, вывести порядок загрузки и граф."""
    try:
        args = parse_config(argv)
    except ConfigError as exc:
        return report_error(exc, CONFIG_ERROR_CODE)
    try:
        graph, cycles, labels = collect_graph(args)
        for line in format_load_order(graph, cycles, labels):
            print(line)
        visualize(args, graph, labels)
    except DATA_ERRORS as exc:
        return report_error(exc, DATA_ERROR_CODE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
