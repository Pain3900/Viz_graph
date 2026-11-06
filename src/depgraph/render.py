"""Визуализация графа: текст Mermaid, ASCII-дерево, изображение SVG.

Изображение рисует сервис mermaid.ink: текст Mermaid кодируется в
base64 и передаётся в адресе запроса, в ответ приходит SVG.
"""

import base64
import urllib.error
import urllib.request

MERMAID_INK_URL = "https://mermaid.ink/svg/"
USER_AGENT = "Mozilla/5.0 (compatible; depgraph)"
TIMEOUT_SECONDS = 30
BRANCH = "├── "
LAST_BRANCH = "└── "
INDENT = "│   "
LAST_INDENT = "    "


class RenderError(Exception):
    """Не удалось получить или сохранить изображение графа."""


def to_mermaid(graph, labels):
    """Вернуть строки описания графа на языке Mermaid.

    Узлы получают идентификаторы n1, n2, ... в порядке обхода, имя
    пакета записывается подписью: символы ``@ / .`` в идентификаторах
    Mermaid недопустимы.
    """
    ids = {name: f"n{number}" for number, name in enumerate(graph, 1)}
    lines = ["graph TD"]
    for name in graph:
        lines.append(f'    {ids[name]}["{labels.get(name, name)}"]')
    for name, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"    {ids[name]} --> {ids[dependency]}")
    return lines


def push_children(stack, children, prefix, ancestors):
    """Положить зависимости в стек так, чтобы первая вышла первой."""
    for index in reversed(range(len(children))):
        is_last = index == len(children) - 1
        stack.append((children[index], prefix, is_last, ancestors))


def ascii_tree(graph, root, labels):
    """Вернуть строки ASCII-дерева зависимостей (обход без рекурсии).

    Пакет с зависимостями, уже показанный выше, помечается
    ``(see above)``; зависимость, замыкающая цикл, - ``(cycle)``.
    """
    lines = [labels.get(root, root)]
    shown = {root}
    stack = []
    push_children(stack, graph[root], "", (root,))
    while stack:
        name, prefix, is_last, ancestors = stack.pop()
        line = prefix + (LAST_BRANCH if is_last else BRANCH)
        line += labels.get(name, name)
        if name in ancestors:
            lines.append(line + " (cycle)")
        elif name in shown and graph[name]:
            lines.append(line + " (see above)")
        else:
            lines.append(line)
            shown.add(name)
            child_prefix = prefix + (LAST_INDENT if is_last else INDENT)
            push_children(stack, graph[name], child_prefix,
                          ancestors + (name,))
    return lines


def image_url(mermaid_lines):
    """Вернуть адрес изображения графа в сервисе mermaid.ink."""
    code = "\n".join(mermaid_lines).encode("utf-8")
    return MERMAID_INK_URL + base64.urlsafe_b64encode(code).decode("ascii")


def save_image(mermaid_lines, path):
    """Получить SVG из mermaid.ink и сохранить в файл ``path``."""
    request = urllib.request.Request(
        image_url(mermaid_lines), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS) as response:
            image = response.read()
    except urllib.error.HTTPError as exc:
        exc.close()
        raise RenderError(
            f"cannot render image: HTTP error {exc.code} {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RenderError(f"cannot render image: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RenderError("cannot render image: timed out") from exc
    try:
        with open(path, "wb") as image_file:
            image_file.write(image)
    except OSError as exc:
        raise RenderError(f"cannot write '{path}': {exc.strerror}") from exc
