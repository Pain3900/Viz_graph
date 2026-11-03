#!/bin/sh
# Этап 3: транзитивный граф, фильтр, циклические зависимости.
cd "$(dirname "$0")/.." || exit 1
URL=https://registry.npmjs.org
run() {
    echo "\$ depgraph $*"
    sh run.sh "$@"
    echo "Код завершения: $?"
    echo
}
echo "=== общая зависимость (ромб) ==="
cat repos/simple.txt
echo
run --package A --repo repos/simple.txt --test-mode
run --package B --repo repos/simple.txt --test-mode
echo "=== цикл ==="
cat repos/cycle.txt
echo
run --package A --repo repos/cycle.txt --test-mode
run --package C --repo repos/cycle.txt --test-mode
echo "=== фильтр ==="
cat repos/filter.txt
echo
run --package APP --repo repos/filter.txt --test-mode
run --package APP --repo repos/filter.txt --test-mode --filter TEST
run --package APP --repo repos/filter.txt --test-mode --filter LIB
echo "=== реестр npm ==="
run --package debug --repo "$URL"
run --package accepts --repo "$URL" --filter mime
