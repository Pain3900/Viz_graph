# Визуализатор графа зависимостей npm-пакетов (вариант 15)

Практическая работа №2 по дисциплине «Конфигурационное управление».
Консольное приложение (CLI) на Python для анализа и визуализации графа
зависимостей пакетов JavaScript (npm). Готовые менеджеры пакетов и
библиотеки для получения зависимостей не используются.

Текущий этап — **Этап 1. Минимальный прототип с конфигурацией**:
приложение принимает параметры командной строки, проверяет их и
выводит в формате `ключ=значение`.

## Структура проекта

```
src/depgraph/
    __main__.py   точка входа (python -m depgraph)
    config.py     параметры командной строки и их проверка
tests/            модульные тесты (unittest)
scripts/          скрипты для демонстрации работы
repos/            тестовые репозитории
run.sh, run.bat   запуск приложения
test.sh, test.bat запуск тестов
```

## Параметры

| Опция | Обязательная | Описание |
|-------|--------------|----------|
| `--package ИМЯ` | да | имя анализируемого пакета |
| `--repo URL_ИЛИ_ПУТЬ` | да | URL репозитория пакетов или, в тестовом режиме, путь к файлу тестового репозитория |
| `--test-mode` | нет | работать с тестовым репозиторием из файла |
| `--ascii-tree` | нет | выводить зависимости в виде ASCII-дерева |
| `--filter ПОДСТРОКА` | нет | не учитывать пакеты, имя которых содержит подстроку |

При запуске все параметры выводятся в формате `ключ=значение`;
не заданный фильтр выводится как `(not set)`, флаги — как `true`
или `false`.

### Проверка параметров

| Параметр | Правило |
|----------|---------|
| `--package` | непустое; в обычном режиме — имя по правилам npm: маленькие буквы, цифры, `-`, `.`, `_`, `~`, не начинается с `.` или `_`, допускается область видимости `@scope/имя`, не длиннее 214 символов; в тестовом режиме — только большие латинские буквы (`A`, `B`, `AB`) |
| `--repo` | непустое; в обычном режиме — URL со схемой `http` или `https` и адресом сервера; в тестовом режиме — путь к существующему файлу |
| `--test-mode`, `--ascii-tree` | флаги, значений не принимают |
| `--filter` | непустая подстрока без пробелов |

Ошибка выводится в поток ошибок, приложение завершается с кодом 2:

| Запуск | Сообщение |
|--------|-----------|
| без `--package` | `depgraph: error: the following arguments are required: --package` |
| `--package React` | `depgraph: error: --package: name must be lowercase: 'React'` |
| `--package .hidden` | `depgraph: error: --package: invalid npm package name: '.hidden'` |
| `--package a --test-mode` | `depgraph: error: --package: in test mode name must consist of capital Latin letters: 'a'` |
| `--repo registry.npmjs.org` | `depgraph: error: --repo: expected http:// or https:// URL, got 'registry.npmjs.org'` |
| `--repo missing.txt --test-mode` | `depgraph: error: --repo: file not found: 'missing.txt'` |
| `--repo repos --test-mode` | `depgraph: error: --repo: not a file: 'repos'` |
| `--ascii-tree=1` | `depgraph: error: argument --ascii-tree: ignored explicit argument '1'` |
| `--filter ""` | `depgraph: error: --filter: substring must not be empty` |
| `--filter "a b"` | `depgraph: error: --filter: substring must not contain spaces: 'a b'` |
| `--depth 2` | `depgraph: error: unrecognized arguments: --depth 2` |

## Сборка и запуск

Требуется Python 3.8+, сторонние библиотеки не нужны.

```sh
sh run.sh --package ИМЯ --repo URL [--test-mode] [--ascii-tree] [--filter ПОДСТРОКА]
run.bat --package ИМЯ --repo URL ...      # Windows
```

Запуск тестов:

```sh
sh test.sh        # Linux / macOS
test.bat          # Windows
```

Демонстрация:

```sh
sh scripts/demo_ok.sh       # корректные запуски
sh scripts/demo_errors.sh   # ошибки для каждого параметра
```

## Примеры использования

```
$ sh run.sh --package react --repo https://registry.npmjs.org
package=react
repo=https://registry.npmjs.org
test_mode=false
ascii_tree=false
filter=(not set)

$ sh run.sh --package A --repo repos/simple.txt --test-mode --ascii-tree
package=A
repo=repos/simple.txt
test_mode=true
ascii_tree=true
filter=(not set)

$ sh run.sh --package React --repo https://registry.npmjs.org
depgraph: error: --package: name must be lowercase: 'React'
```
