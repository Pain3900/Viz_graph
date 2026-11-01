# Визуализатор графа зависимостей npm-пакетов (вариант 15)

Практическая работа №2 по дисциплине «Конфигурационное управление».
Консольное приложение (CLI) на Python для анализа и визуализации графа
зависимостей пакетов JavaScript (npm). Готовые менеджеры пакетов и
библиотеки для получения зависимостей не используются.

Текущий этап — **Этап 2. Сбор данных**: приложение получает прямые
зависимости пакета из реестра npm (или из файла тестового
репозитория) и выводит их. На Этапе 1 приложение выводило параметры
в формате `ключ=значение`; начиная с Этапа 2 этот вывод убран.

## Структура проекта

```
src/depgraph/
    __main__.py   точка входа (python -m depgraph)
    config.py     параметры командной строки и их проверка
    registry.py   запрос метаданных пакета к реестру npm
    repo_file.py  чтение тестового репозитория из файла
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

Параметры `--ascii-tree` и `--filter` проверяются, но используются
начиная с Этапов 3 и 5.

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

## Сбор данных (Этап 2)

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
учитываются. dev-зависимости npm не устанавливает у пакетов, которые
сами стоят как зависимости; peer- и optional-зависимости npm
обрабатывает по отдельным правилам, расхождения с npm разбираются на
Этапе 4. Зависимости из реестра выводятся по алфавиту.

В тестовом режиме (`--test-mode`) зависимости читаются из файла.
Каждая строка: имя пакета, двоеточие и прямые зависимости через
пробел; имена — большие латинские буквы; пустые строки пропускаются.

```
A: B C
B: D
C: D
D:
```

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
sh scripts/demo_stage2.sh   # Этап 2: зависимости и ошибки получения данных
```

## Примеры использования

Версии и списки зависимостей зависят от момента запуска.

```
$ sh run.sh --package express --repo https://registry.npmjs.org
Direct dependencies of express@5.3.0:
  accepts ^2.0.0
  body-parser ^2.3.0
  ...
  vary ^1.1.2

$ sh run.sh --package lodash --repo https://registry.npmjs.org
Direct dependencies of lodash@4.18.1:
  (none)

$ sh run.sh --package A --repo repos/simple.txt --test-mode
Direct dependencies of A:
  B
  C

$ sh run.sh --package no-such-package-depgraph --repo https://registry.npmjs.org
depgraph: error: package not found: 'no-such-package-depgraph'

$ sh run.sh --package React --repo https://registry.npmjs.org
depgraph: error: --package: name must be lowercase: 'React'
```
