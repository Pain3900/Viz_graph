# Визуализатор графа зависимостей npm-пакетов (вариант 15)

Практическая работа №2 по дисциплине «Конфигурационное управление».
Консольное приложение (CLI) на Python для анализа и визуализации графа
зависимостей пакетов JavaScript (npm). Готовые менеджеры пакетов и
библиотеки для получения зависимостей не используются.

Текущий этап — **Этап 3. Основные операции**: приложение строит граф
зависимостей пакета с учётом транзитивности, исключает пакеты по
подстроке фильтра, находит циклические зависимости и выводит граф
списком смежности.

| Этап | Что выводит приложение |
|------|------------------------|
| 1 | параметры в формате `ключ=значение` |
| 2 | прямые зависимости пакета |
| 3 | граф зависимостей и найденные циклы |

## Структура проекта

```
src/depgraph/
    __main__.py   точка входа (python -m depgraph)
    config.py     параметры командной строки и их проверка
    registry.py   запрос метаданных пакета к реестру npm
    repo_file.py  чтение тестового репозитория из файла
    graph.py      построение графа (DFS без рекурсии)
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

Параметр `--ascii-tree` проверяется, но используется начиная с
Этапа 5.

### Проверка параметров

| Параметр | Правило |
|----------|---------|
| `--package` | непустое; в обычном режиме — имя по правилам npm: маленькие буквы, цифры, `-`, `.`, `_`, `~`, не начинается с `.` или `_`, допускается область видимости `@scope/имя`, не длиннее 214 символов; в тестовом режиме — только большие латинские буквы (`A`, `B`, `AB`) |
| `--repo` | непустое; в обычном режиме — URL со схемой `http` или `https` и адресом сервера; в тестовом режиме — путь к существующему файлу |
| `--test-mode`, `--ascii-tree` | флаги, значений не принимают |
| `--filter` | непустая подстрока без пробелов |

Ошибка параметра выводится в поток ошибок, приложение завершается
с кодом 2:

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

## Сбор данных

Метаданные пакета запрашиваются модулем `urllib.request` из
стандартной библиотеки по адресу `{repo}/{имя}`, например
`https://registry.npmjs.org/express`. В имени с областью видимости
косая черта кодируется: `@babel/core` → `@babel%2Fcore`.

Запрос отправляется с заголовком
`Accept: application/vnd.npm.install-v1+json`. Реестр тогда отдаёт
сокращённые метаданные без README и описаний: для крупных пакетов
это сотни килобайт вместо десятков мегабайт. Из ответа берётся:

- версия из `dist-tags.latest`;
- поле `dependencies` этой версии: имя зависимости и диапазон версий.

`devDependencies`, `peerDependencies` и `optionalDependencies` не
учитываются. Каждый пакет в графе представлен один раз, в версии
`latest`; диапазоны версий из `dependencies` не разрешаются.
Расхождения с npm разбираются на Этапе 4. Зависимости из реестра
обходятся по алфавиту.

Ошибки получения данных выводятся в поток ошибок, код завершения 1:

| Ситуация | Сообщение |
|----------|-----------|
| пакета нет в реестре (HTTP 404) | `depgraph: error: package not found: 'имя'` |
| другой ответ HTTP | `depgraph: error: HTTP error 500 Internal Server Error for URL` |
| сервер недоступен | `depgraph: error: cannot connect to URL: причина` |
| истекло время ожидания (15 с) | `depgraph: error: timed out while reading URL` |
| ответ не JSON | `depgraph: error: invalid JSON in response from URL` |
| нет версии `latest` | `depgraph: error: no 'latest' version for 'имя'` |
| версии `latest` нет в `versions` | `depgraph: error: version X of 'имя' is missing in metadata` |
| строка файла без двоеточия | `depgraph: error: ФАЙЛ:N: expected 'NAME: DEPENDENCIES'` |
| неверное имя в файле | `depgraph: error: ФАЙЛ:N: invalid package name 'a'` |
| пакет описан дважды | `depgraph: error: ФАЙЛ:N: package 'A' is defined twice` |
| пакета нет в файле | `depgraph: error: package not found in test repository: 'Z'` |

## Тестовый репозиторий

В тестовом режиме (`--test-mode`) граф читается из файла, реестр не
нужен. Каждая строка: имя пакета, двоеточие и прямые зависимости
через пробел. Имена — большие латинские буквы, пустые строки
пропускаются. Пакет, который указан как зависимость, но не описан
отдельной строкой, считается пакетом без зависимостей. Анализируемый
пакет (`--package`) в файле описан быть обязан.

| Файл | Что показывает |
|------|----------------|
| `repos/simple.txt` | общая зависимость (ромб): `D` нужен и `B`, и `C` |
| `repos/cycle.txt` | цикл `A -> B -> C -> A` |
| `repos/filter.txt` | фильтр: `--filter TEST` убирает `TESTLIB` вместе с тем, что нужно только ему |
| `repos/broken.txt` | ошибка формата файла |

`repos/simple.txt`:

```
A: B C
B: D
C: D
D:
```

## Построение графа

Граф строится обходом в глубину (DFS) без рекурсии (`graph.py`,
функция `build_graph`): вместо стека вызовов используется список, в
котором для каждого открытого пакета хранится итератор по его
зависимостям. Поэтому глубина графа не ограничена лимитом рекурсии
Python; это проверяет тест с цепочкой вдвое длиннее этого лимита. Зависимости
каждого пакета запрашиваются один раз, даже если пакет нужен
нескольким другим.

Фильтр `--filter` исключает пакет, если его имя содержит подстроку
(с учётом регистра). Исключённый пакет не обходится, поэтому его
зависимости попадают в граф только если нужны другим пакетам.
Анализируемый пакет фильтром не исключается.

Каждый пакет при обходе находится в одном из состояний: не встречен,
открыт (сейчас на пути от корня) или обработан. Если зависимость
указывает на открытый пакет, это цикл: обход по такому ребру не
продолжается, цикл выводится строкой `Cycle: ...`, а ребро остаётся в
графе. Если зависимость указывает на уже обработанный пакет, это не
цикл, а общая зависимость.

Вывод: пакеты в порядке обнаружения, у каждого — прямые зависимости
после фильтра; пакеты из реестра подписаны версией.

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
sh scripts/demo_stage2.sh   # Этап 2: данные из реестра и файла, ошибки
sh scripts/demo_stage3.sh   # Этап 3: ромб, цикл, фильтр, реестр npm
```

## Примеры использования

Версии пакетов из реестра зависят от момента запуска.

```
$ sh run.sh --package A --repo repos/simple.txt --test-mode
Dependency graph of A (packages: 4):
  A -> B, C
  B -> D
  D -> (none)
  C -> D

$ sh run.sh --package A --repo repos/cycle.txt --test-mode
Dependency graph of A (packages: 4):
  A -> B
  B -> C
  C -> A, D
  D -> (none)
Cycle: A -> B -> C -> A

$ sh run.sh --package APP --repo repos/filter.txt --test-mode --filter TEST
Dependency graph of APP (packages: 3):
  APP -> LIB
  LIB -> CORE
  CORE -> (none)

$ sh run.sh --package debug --repo https://registry.npmjs.org
Dependency graph of debug@4.4.3 (packages: 2):
  debug@4.4.3 -> ms
  ms@2.1.3 -> (none)

$ sh run.sh --package no-such-package-depgraph --repo https://registry.npmjs.org
depgraph: error: package not found: 'no-such-package-depgraph'

$ sh run.sh --package React --repo https://registry.npmjs.org
depgraph: error: --package: name must be lowercase: 'React'
```
