"""Тесты построения графа зависимостей (DFS без рекурсии)."""

import sys
import unittest

from depgraph.graph import build_graph


def source(packages):
    """Функция зависимостей по словарю; считает обращения к пакетам."""
    calls = []

    def get_dependencies(name):
        calls.append(name)
        return packages.get(name, [])
    get_dependencies.calls = calls
    return get_dependencies


class BuildGraphTest(unittest.TestCase):
    """Транзитивные зависимости, фильтр и циклы."""

    def test_shared_dependency(self):
        """Общая зависимость (ромб) запрашивается один раз."""
        get = source({"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []})
        graph, cycles = build_graph("A", get)
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["D"],
                                 "D": [], "C": ["D"]})
        self.assertEqual(list(graph), ["A", "B", "D", "C"])
        self.assertEqual(cycles, [])
        self.assertEqual(sorted(get.calls), ["A", "B", "C", "D"])

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        self.assertEqual(build_graph("A", source({})), ({"A": []}, []))

    def test_cycle(self):
        """Цикл находится, обход завершается."""
        get = source({"A": ["B"], "B": ["C"], "C": ["A", "D"]})
        graph, cycles = build_graph("A", get)
        self.assertEqual(set(graph), {"A", "B", "C", "D"})
        self.assertEqual(graph["C"], ["A", "D"])
        self.assertEqual(cycles, [["A", "B", "C", "A"]])

    def test_self_dependency(self):
        """Пакет зависит сам от себя."""
        graph, cycles = build_graph("A", source({"A": ["A", "B"]}))
        self.assertEqual(graph, {"A": ["A", "B"], "B": []})
        self.assertEqual(cycles, [["A", "A"]])

    def test_two_cycles(self):
        """Два цикла через один пакет."""
        get = source({"A": ["B", "C"], "B": ["A"], "C": ["A"]})
        self.assertEqual(build_graph("A", get)[1],
                         [["A", "B", "A"], ["A", "C", "A"]])

    def test_visited_is_not_cycle(self):
        """Повторная встреча уже обработанного пакета - не цикл."""
        get = source({"A": ["B", "C"], "B": ["C"], "C": []})
        self.assertEqual(build_graph("A", get)[1], [])

    def test_filter(self):
        """Пакет с подстрокой исключается вместе со своим поддеревом."""
        get = source({"APP": ["LIB", "TESTLIB"], "LIB": ["CORE"],
                      "TESTLIB": ["CORE", "MOCK"]})
        graph, _ = build_graph("APP", get, "TEST")
        self.assertEqual(graph, {"APP": ["LIB"], "LIB": ["CORE"],
                                 "CORE": []})
        self.assertNotIn("TESTLIB", get.calls)

    def test_filter_keeps_root(self):
        """Корневой пакет фильтром не исключается."""
        graph, _ = build_graph("LIB", source({"LIB": ["LIBX", "A"]}), "LIB")
        self.assertEqual(graph, {"LIB": ["A"], "A": []})

    def test_deep_chain_without_recursion(self):
        """Цепочка длиннее лимита рекурсии Python."""
        length = sys.getrecursionlimit() * 2
        packages = {f"P{i}": [f"P{i + 1}"] for i in range(length)}
        graph, cycles = build_graph("P0", source(packages))
        self.assertEqual(len(graph), length + 1)
        self.assertEqual(cycles, [])


if __name__ == "__main__":
    unittest.main()
