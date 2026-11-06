#!/bin/sh
# Этап 5: Mermaid, ASCII-дерево, изображение; примеры в папке examples/.
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
run --package A --repo repos/cycle.txt --test-mode --ascii-tree
run --package APP --repo repos/filter.txt --test-mode --ascii-tree \
    --filter TEST
echo "=== примеры для трёх пакетов (папка examples/) ==="
mkdir -p examples
for name in debug accepts body-parser; do
    sh run.sh --package "$name" --repo "$URL" \
        --image "examples/$name.svg" \
        | sed -n '/^graph TD/,$p' > "examples/$name.mmd"
    sh run.sh --package "$name" --repo "$URL" --ascii-tree \
        > "examples/$name.txt"
    echo "$name: examples/$name.mmd, examples/$name.svg, examples/$name.txt"
done
