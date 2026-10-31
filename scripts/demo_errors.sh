#!/bin/sh
# Этап 1: обработка ошибок для каждого параметра.
cd "$(dirname "$0")/.." || exit 1
URL=https://registry.npmjs.org
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
    sh run.sh "$@" 2>&1 | tail -n 1
    echo
}
echo "=== --package ==="
run --repo "$URL"
run --package "" --repo "$URL"
run --package React --repo "$URL"
run --package .hidden --repo "$URL"
run --package a --repo repos/simple.txt --test-mode
echo "=== --repo ==="
run --package react
run --package react --repo ""
run --package react --repo registry.npmjs.org
run --package react --repo ftp://example.org
run --package A --repo repos/missing.txt --test-mode
run --package A --repo repos --test-mode
echo "=== --test-mode и --ascii-tree ==="
run --package react --repo "$URL" --test-mode=yes
run --package react --repo "$URL" --ascii-tree=1
echo "=== --filter ==="
run --package react --repo "$URL" --filter
run --package react --repo "$URL" --filter ""
run --package react --repo "$URL" --filter "a b"
echo "=== неизвестный параметр ==="
run --package react --repo "$URL" --depth 2
