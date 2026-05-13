# Раздел 3: Автоматизация с помощью Ansible

В этом разделе реализована автоматизация установки Docker и проверки работы контейнера с Python-скриптом через Ansible.

Стенд состоит из двух виртуальных машин:

* `vm1` — control-node, с него запускается Ansible;
* `vm2` — target-node, на него Ansible подключается по SSH и выполняет настройку.

Такой вариант выбран вместо запуска на `localhost`, потому что он лучше показывает реальную схему работы Ansible: управляющий узел подключается к целевому хосту и приводит его к нужному состоянию.

## Структура раздела

```text
section3-ansible/
├── ansible.cfg
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   └── docker_hosts.yml
│   └── host_vars/
├── roles/
│   ├── docker/
│   │   ├── defaults/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── tasks/
│   │       └── main.yml
│   └── httpstat_container/
│       ├── defaults/
│       │   └── main.yml
│       ├── files/
│       │   └── build_context/
│       │       ├── Dockerfile
│       │       ├── .dockerignore
│       │       ├── httpstat_checker.py
│       │       └── requirements.txt
│       └── tasks/
│           └── main.yml
└── site.yml
```

## Что делает playbook

Playbook `site.yml` состоит из двух частей.

Первая часть устанавливает и настраивает Docker на целевом хосте:

* проверяет, что целевая система — Ubuntu;
* определяет архитектуру системы для Docker apt-репозитория;
* устанавливает зависимости для подключения официального Docker-репозитория;
* добавляет GPG-ключ Docker;
* добавляет официальный Docker apt-репозиторий;
* устанавливает Docker-пакеты;
* добавляет пользователя в группу `docker`;
* запускает и включает службу `docker.service`;
* проверяет установку командой `docker --version`.

Вторая часть собирает и запускает контейнер с HTTP status checker:

* копирует Docker build context на целевой хост;
* проверяет, существует ли Docker-образ;
* собирает Docker-образ, если образ отсутствует или изменился build context;
* удаляет старый контейнер, если он уже существует;
* запускает новый контейнер;
* получает результат через `docker logs`;
* проверяет exit code контейнера;
* проверяет наличие ожидаемой строки в логах.

## Использованные best practices

В решении применены следующие практики:

* используется отдельный `inventory`;
* переменные группы вынесены в `inventory/group_vars`;
* логика разделена на роли:

  * `docker` — установка и настройка Docker;
  * `httpstat_container` — сборка, запуск и проверка контейнера;
* `site.yml` используется как точка входа, а не как один большой файл со всеми задачами;
* `become: true` используется только там, где нужны root-права;
* запуск контейнера выполняется от обычного пользователя, добавленного в группу `docker`;
* после добавления пользователя в группу `docker` выполняется `meta: reset_connection`, чтобы новое подключение увидело обновлённые группы пользователя;
* для проверки результата используются `docker logs`, exit code контейнера и Ansible `assert`;
* Docker-образ не пересобирается без необходимости: сначала проверяется наличие образа и изменение build context.

## Идемпотентность

Инфраструктурная часть playbook идемпотентна: повторный запуск не переустанавливает Docker, не пересоздаёт apt-репозиторий и не меняет системные настройки без необходимости.

Проверочная часть намеренно запускает контейнер заново при каждом выполнении playbook. Это сделано потому, что по заданию нужно проверить выполнение скрипта внутри контейнера и получить свежий результат через `docker logs`.

Поэтому при повторном запуске нормальна ситуация, когда изменяются только задачи удаления старого контейнера и запуска нового контейнера. Это не ошибка идемпотентности, а часть проверки работоспособности.

## Inventory

Пример `inventory/hosts.yml`:

```yaml
---
all:
  children:
    docker_hosts:
      hosts:
        docker-target:
          ansible_host: 192.168.56.103
          ansible_user: worker
          ansible_port: 22
          ansible_python_interpreter: /usr/bin/python3
```

Пример `inventory/group_vars/docker_hosts.yml`:

```yaml
---
docker_user: "{{ ansible_user }}"

docker_image_name: httpstat-checker
docker_image_tag: ansible
docker_container_name: httpstat-checker

docker_build_context_dest: "/home/{{ docker_user }}/httpstat-checker-docker-context"

httpstat_success_marker: "All requests were processed"
```

## Проверка inventory

```bash
ansible-inventory --graph
```

Ожидаемый результат:

```text
@all:
  |--@ungrouped:
  |--@docker_hosts:
  |  |--docker-target
```

## Проверка подключения к target-node

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

## Проверка синтаксиса playbook

```bash
ansible-playbook site.yml --syntax-check
```

Ожидаемый результат:

```text
playbook: site.yml
```

## Запуск playbook

```bash
ansible-playbook site.yml -K
```

Флаг `-K` нужен, потому что установка Docker и настройка службы требуют sudo-права.

## Проверка результата

После успешного запуска playbook можно отдельно проверить контейнер:

```bash
ansible docker_hosts -m command -a "docker ps -a"
```

Проверить логи контейнера:

```bash
ansible docker_hosts -m command -a "docker logs httpstat-checker"
```

В логах должны быть успешные ответы для `200`, `201`, `301`, обработанные ошибки для `404` и `500`, а также финальная строка:

```text
All requests were processed
```

Успешное выполнение playbook подтверждается строкой в `PLAY RECAP`:

```text
failed=0
```

Пример успешного результата:

```text
docker-target : ok=23 changed=3 unreachable=0 failed=0 skipped=0 rescued=0 ignored=
```
