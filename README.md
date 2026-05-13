# HTTP Status Automation Task

Проект выполнен в рамках тестового задания по пошаговой автоматизации с использованием Python, Docker и Ansible.

Задание разделено на три последовательных части:

1. разработка скрипта для HTTP-запросов;
2. упаковка скрипта в Docker-образ;
3. автоматизация установки Docker и проверки контейнера через Ansible.

Каждый раздел находится в отдельной директории и фиксируется отдельным коммитом в ветке `master`.

## Структура проекта

```text
httpstat-automation-task/
├── section1-script/
│   ├── httpstat_checker.py
│   └── requirements.txt
├── section2-docker/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── httpstat_checker.py
│   └── README.md
├── section3-ansible/
│   ├── ansible.cfg
│   ├── inventory/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   │   └── docker_hosts.yml
│   │   └── host_vars/
│   ├── roles/
│   │   ├── docker/
│   │   │   ├── defaults/
│   │   │   │   └── main.yml
│   │   │   ├── handlers/
│   │   │   │   └── main.yml
│   │   │   └── tasks/
│   │   │       └── main.yml
│   │   └── httpstat_container/
│   │       ├── defaults/
│   │       │   └── main.yml
│   │       ├── files/
│   │       │   └── build_context/
│   │       │       ├── Dockerfile
│   │       │       ├── .dockerignore
│   │       │       ├── httpstat_checker.py
│   │       │       └── requirements.txt
│   │       └── tasks/
│   │           └── main.yml
│   ├── site.yml
│   └── README.md
├── .dockerignore
├── .gitignore
└── README.md
```

## Раздел 1: Работа со скриптом

В первом разделе реализован Python-скрипт `httpstat_checker.py`.

Скрипт выполняет 5 HTTP-запросов к сервису проверки HTTP-статусов:

```text
https://tools-httpstatus.pickup-services.com
```

Исходный сервис `https://httpstat.us` был заменён, так как на момент выполнения задания он работал нестабильно.

Скрипт проверяет следующие статус-коды:

* `200`;
* `201`;
* `301`;
* `404`;
* `500`.

Логика обработки:

* для `1xx`, `2xx`, `3xx` логируется статус-код и тело ответа;
* для `4xx`, `5xx` создаётся исключительная ситуация;
* исключения обрабатываются внутри программы и логируются в консоль;
* после обработки всех запросов скрипт завершается с кодом `0`.

### Запуск первого раздела

```bash
cd section1-script
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python httpstat_checker.py
```

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

## Раздел 2: Работа с Docker

Во втором разделе скрипт из первого раздела упакован в Docker-образ.

Образ собирается на базе официального `ubuntu:22.04`, закреплённого через `sha256` digest.

Dockerfile выполняет следующие действия:

* устанавливает необходимые зависимости;
* копирует Python-скрипт в контейнер;
* создаёт непривилегированного пользователя;
* запускает скрипт при старте контейнера.

### Использованные Docker best practices

* официальный базовый образ `ubuntu:22.04`;
* базовый образ закреплён через `sha256` digest;
* используется `COPY`, а не `ADD`;
* зависимости устанавливаются через один `RUN`;
* используется `--no-install-recommends`;
* после установки пакетов очищается apt cache;
* контейнер запускается не от root-пользователя;
* лишние файлы исключены через `.dockerignore`.

### Сборка Docker-образа

Команда выполняется из корня репозитория:

```bash
docker build -t httpstat-checker:1.0.0 section2-docker
```

### Запуск контейнера

```bash
docker run --name httpstat-checker-test httpstat-checker:1.0.0
```

Если контейнер уже существует:

```bash
docker rm httpstat-checker-test
docker run --name httpstat-checker-test httpstat-checker:1.0.0
```

### Проверка через docker logs

```bash
docker logs httpstat-checker-test
```

### Проверка кода завершения

```bash
docker inspect httpstat-checker-test --format='{{.State.ExitCode}}'
```

Ожидаемый результат:

```text
0
```

## Раздел 3: Автоматизация с помощью Ansible

В третьем разделе автоматизирован процесс установки Docker и проверки работы контейнера на целевом хосте.

Стенд состоит из двух виртуальных машин:

* `vm1` — control-node, с него запускается Ansible;
* `vm2` — target-node, на него Ansible подключается по SSH.

Ansible выполняет следующие действия:

1. подключается к целевому хосту;
2. устанавливает Docker через официальный apt-репозиторий;
3. добавляет пользователя в группу `docker`;
4. запускает и включает `docker.service`;
5. проверяет установку Docker;
6. копирует Docker build context на target-node;
7. собирает Docker-образ;
8. запускает контейнер;
9. получает результат через `docker logs`;
10. проверяет exit code контейнера и ожидаемый текст в логах.

### Использованные Ansible best practices

* используется отдельный `inventory`;
* переменные вынесены в `group_vars`;
* логика разделена на роли;
* `site.yml` используется как точка входа;
* `become: true` применяется только для задач, где нужны root-права;
* запуск контейнера выполняется от обычного пользователя;
* после добавления пользователя в группу `docker` выполняется `meta: reset_connection`;
* результат проверяется через `assert`;
* Docker-образ не пересобирается без необходимости.

### Подготовка Ansible

На control-node используется отдельное Python-окружение:

```bash
python3 -m venv .ansible-venv
source .ansible-venv/bin/activate
pip install --upgrade pip
pip install ansible
```

Проверка версии:

```bash
ansible --version
```

### Проверка inventory

```bash
cd section3-ansible
ansible-inventory --graph
```

Ожидаемый результат:

```text
@all:
  |--@ungrouped:
  |--@docker_hosts:
  |  |--docker-target
```

### Проверка подключения

```bash
ansible docker_hosts -m ping
```

Ожидаемый результат:

```text
docker-target | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### Проверка синтаксиса playbook

```bash
ansible-playbook site.yml --syntax-check
```

### Запуск playbook

```bash
ansible-playbook site.yml -K
```

Флаг `-K` используется для ввода sudo-пароля, так как установка Docker и настройка службы требуют повышенных прав.

### Проверка результата

```bash
ansible docker_hosts -m command -a "docker ps -a"
```

```bash
ansible docker_hosts -m command -a "docker logs httpstat-checker"
```

В логах должны быть видны ответы для `200`, `201`, `301`, обработанные ошибки для `404` и `500`, а также финальная строка:

```text
All requests were processed
```

Успешное выполнение playbook подтверждается строкой в `PLAY RECAP`:

```text
failed=0
```

## Идемпотентность

Инфраструктурная часть Ansible-playbook идемпотентна: повторный запуск не должен заново устанавливать Docker, пересоздавать репозиторий или менять системные настройки без необходимости.

Проверочная часть намеренно запускает контейнер повторно, потому что по заданию требуется проверить выполнение скрипта внутри контейнера и получить свежий результат через `docker logs`.

Поэтому при повторном запуске допустимо, что изменяются задачи удаления старого контейнера и запуска нового контейнера.

## Git workflow

Работа ведётся в ветке `master`.

Каждый раздел фиксируется отдельным коммитом:

```bash
git add section1-script
git commit -m "feat: add http status checker script"

.git add section2-docker
git commit -m "feat: add dockerized http status checker"

git add section3-ansible
git commit -m "feat: automate docker setup and container check with ansible"
```

Проверка истории:

```bash
git log --oneline --decorate
```

## Итог

В результате проект содержит три независимых, но связанных раздела:

* Python-скрипт для обработки HTTP-статусов;
* Docker-образ для запуска скрипта в контейнере;
* Ansible-автоматизацию установки Docker и проверки контейнера на целевом хосте.

Финальная проверка выполняется через Ansible: контейнер запускается на target-node, результат читается через `docker logs`, а корректность выполнения подтверждается exit code контейнера и проверкой ожидаемой строки в логах.
