# Раздел 2: Docker

В этом разделе подготовлен Docker-образ для запуска Python-скрипта из первого раздела.

Образ собирается на базе `ubuntu:22.04`, при этом базовый образ закреплён через `sha256` digest. Это делает сборку более воспроизводимой: Docker будет использовать конкретную версию образа, а не просто текущий вариант тега `ubuntu:22.04`.

## Что находится в разделе

```text
section2-docker/
├── Dockerfile
├── .dockerignore
├── httpstat_checker.py
└── README.md
```

## Что делает Dockerfile

Dockerfile выполняет следующие действия:

1. Использует официальный образ `ubuntu:22.04`, закреплённый через `sha256`.
2. Устанавливает только необходимые зависимости:
   * `ca-certificates` для корректной работы HTTPS-запросов;
   * `python3` для запуска скрипта;
   * `python3-requests` для выполнения HTTP-запросов.
3. Создаёт непривилегированного пользователя `appuser`.
4. Копирует Python-скрипт внутрь контейнера.
5. Запускает скрипт не от root-пользователя.
6. При старте контейнера автоматически выполняет `httpstat_checker.py`.

## Использованные best practices

В Dockerfile применены следующие практики:

* базовый образ закреплён через `sha256` digest;
* используется `COPY`, а не `ADD`, так как загрузка архивов или файлов по URL не требуется;
* зависимости устанавливаются в одном `RUN`, чтобы не создавать лишние слои;
* после установки пакетов очищается apt cache;
* используется `--no-install-recommends`, чтобы не ставить лишние пакеты;
* приложение запускается от непривилегированного пользователя;
* лишние файлы исключены из контекста сборки через `.dockerignore`.

## Сборка образа

Команда выполняется из корня репозитория:

```bash
docker build -t httpstat-checker:1.0.0 section2-docker
```

## Запуск контейнера

```bash
docker run --name httpstat-checker-test httpstat-checker:1.0.0
```

Если контейнер с таким именем уже существует, его можно удалить и запустить заново:

```bash
docker rm httpstat-checker-test
docker run --name httpstat-checker-test httpstat-checker:1.0.0
```

## Проверка логов

После выполнения контейнера результат работы скрипта можно посмотреть через `docker logs`:

```bash
docker logs httpstat-checker-test
```

В логах должны быть видны успешные ответы для `200`, `201`, `301`, а также обработанные ошибки для `404` и `500`.

Пример ожидаемого результата:

```text
INFO | Requesting https://tools-httpstatus.pickup-services.com/200
INFO | Successful response | status_code=200 | body=200 OK
INFO | Requesting https://tools-httpstatus.pickup-services.com/201
INFO | Successful response | status_code=201 | body=201 Created
INFO | Requesting https://tools-httpstatus.pickup-services.com/301
INFO | Successful response | status_code=301 | body=301 Moved Permanently
ERROR | Handled HTTP exception: HTTP error response | status_code=404 | body=404 Not Found
ERROR | Handled HTTP exception: HTTP error response | status_code=500 | body=500 Internal Server Error
INFO | All requests were processed
```

## Проверка кода завершения

```bash
docker inspect httpstat-checker-test --format='{{.State.ExitCode}}'
```

Ожидаемый результат:

```text
0
```

Код завершения `0` означает, что скрипт выполнился корректно. Ошибки `404` и `500` были ожидаемо обработаны внутри программы как исключительные ситуации, поэтому контейнер не завершается с ошибкой.
