#!/bin/sh
# Этап 4: порядок загрузки зависимостей.
cd "$(dirname "$0")/.." || exit 1
URL=https://registry.npmjs.org
run() {
    echo "\$ depgraph $*"
    sh run.sh "$@"
    echo "Код завершения: $?"
    echo
}
echo "=== тестовые репозитории ==="
run --package A --repo repos/simple.txt --test-mode
run --package A --repo repos/cycle.txt --test-mode
run --package C --repo repos/cycle.txt --test-mode
run --package APP --repo repos/filter.txt --test-mode
run --package APP --repo repos/filter.txt --test-mode --filter TEST
echo "=== обратные зависимости: кто зависит от пакета ==="
run --package D --repo repos/simple.txt --test-mode --reverse
run --package A --repo repos/cycle.txt --test-mode --reverse
run --package CORE --repo repos/filter.txt --test-mode --reverse
run --package CORE --repo repos/filter.txt --test-mode --reverse --filter TEST
run --package ms --repo "$URL" --reverse
echo "=== реестр npm ==="
run --package debug --repo "$URL"
run --package accepts --repo "$URL"
