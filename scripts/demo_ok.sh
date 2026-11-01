#!/bin/sh
# Корректные запуски: прямые зависимости пакетов (нужен интернет).
cd "$(dirname "$0")/.." || exit 1
# Печатает команду; пустые значения и значения с пробелами - в кавычках.
show() {
    line="\$ depgraph"
    for arg in "$@"; do
        case "$arg" in
            "" | *" "*) line="$line '$arg'" ;;
            *) line="$line $arg" ;;
        esac
    done
    echo "$line"
}
run() {
    show "$@"
    sh run.sh "$@"
    echo "Код завершения: $?"
    echo
}
run --package react --repo https://registry.npmjs.org
run --package @babel/core --repo https://registry.npmjs.org \
    --ascii-tree --filter test
run --package A --repo repos/simple.txt --test-mode --ascii-tree
