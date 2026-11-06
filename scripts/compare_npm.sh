#!/bin/sh
# Сравнение с npm: порядок запросов npm install и дерево npm ls.
# Запуск: sh scripts/compare_npm.sh ИМЯ_ПАКЕТА (нужен Node.js с npm).
if [ -z "$1" ]; then
    echo "usage: sh scripts/compare_npm.sh PACKAGE" >&2
    exit 2
fi
if ! command -v npm > /dev/null; then
    echo "npm not found: install Node.js from https://nodejs.org" >&2
    exit 1
fi
cd "$(dirname "$0")/.." || exit 1
PROJECT=$(pwd)
WORK=$(mktemp -d)
echo "=== depgraph ==="
sh run.sh --package "$1" --repo https://registry.npmjs.org
cd "$WORK" || exit 1
npm init -y > /dev/null
echo
echo "=== npm install: запросы к реестру по порядку ==="
npm install "$1" --no-audit --no-fund --prefer-online --loglevel http 2>&1 \
    | grep -E "GET (200|304)" | sed -E "s/^npm http fetch GET [0-9]+ //; s/ [0-9]+ms.*//"
echo
echo "=== npm ls --all ==="
npm ls --all
cd "$PROJECT" && rm -rf "$WORK"
