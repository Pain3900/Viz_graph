#!/bin/sh
# Этап 2: данные из реестра npm и из тестового файла, ошибки получения данных.
cd "$(dirname "$0")/.." || exit 1
URL=https://registry.npmjs.org
run() {
    echo "\$ depgraph $*"
    sh run.sh "$@"
    echo "Код завершения: $?"
    echo
}
echo "=== реестр npm ==="
run --package express --repo "$URL"
run --package @babel/core --repo "$URL"
run --package lodash --repo "$URL"
echo "=== тестовый репозиторий ==="
run --package A --repo repos/simple.txt --test-mode
run --package D --repo repos/simple.txt --test-mode
echo "=== ошибки ==="
run --package no-such-package-depgraph --repo "$URL"
run --package react --repo https://no-such-host.invalid
run --package Z --repo repos/simple.txt --test-mode
run --package A --repo repos/broken.txt --test-mode
