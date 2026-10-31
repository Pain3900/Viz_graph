"""Точка входа: ``python -m depgraph --package ИМЯ --repo URL``."""

import sys

from depgraph.config import PROGRAM_NAME, ConfigError, parse_config
from depgraph.config import format_config

CONFIG_ERROR_CODE = 2


def main(argv=None):
    """Разобрать параметры, вывести их и вернуть код завершения."""
    try:
        args = parse_config(argv)
    except ConfigError as exc:
        print(f"{PROGRAM_NAME}: error: {exc}", file=sys.stderr)
        return CONFIG_ERROR_CODE
    for line in format_config(args):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
