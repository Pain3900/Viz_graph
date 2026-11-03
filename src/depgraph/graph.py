"""Граф зависимостей с учётом транзитивности.

Граф строится обходом в глубину без рекурсии: вместо стека вызовов
используется список итераторов по зависимостям открытых пакетов,
поэтому глубина графа не ограничена лимитом рекурсии Python.
"""

OPEN = "open"
DONE = "done"


def keep_unfiltered(names, name_filter):
    """Убрать пакеты, имя которых содержит подстроку фильтра."""
    if not name_filter:
        return list(names)
    return [name for name in names if name_filter not in name]


def build_graph(root, get_dependencies, name_filter=None):
    """Построить граф зависимостей пакета ``root``.

    ``get_dependencies(имя)`` возвращает прямые зависимости пакета и
    вызывается для каждого пакета один раз. Корневой пакет фильтром
    не исключается.

    Возвращает (граф, циклы). Граф - словарь ``имя -> [зависимости]``,
    пакеты в нём идут в порядке обнаружения. Цикл - список имён от
    пакета, на котором цикл начался, до него же.
    """
    graph = {root: keep_unfiltered(get_dependencies(root), name_filter)}
    state = {root: OPEN}
    path = [root]
    stack = [iter(graph[root])]
    cycles = []
    while stack:
        dependency = next(stack[-1], None)
        if dependency is None:
            stack.pop()
            state[path.pop()] = DONE
        elif dependency not in state:
            graph[dependency] = keep_unfiltered(
                get_dependencies(dependency), name_filter)
            state[dependency] = OPEN
            path.append(dependency)
            stack.append(iter(graph[dependency]))
        elif state[dependency] == OPEN:
            start = path.index(dependency)
            cycles.append(path[start:] + [dependency])
    return graph, cycles
