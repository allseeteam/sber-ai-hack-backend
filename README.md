# Sber AI Hackathon 2025

В данном репозитории содержится код бекенда для кейса "Агент Function Matcher", разработанный командой [AllSee.team](https://allSee.team).

## Структура репозитория

```
.env.example
.gitignore
docker-compose.yml
Dockerfile
README.md
requirements.txt
sourcebot-config.json # Конфигурационный файл со списком репозиториев
code-search-api/      # API для векторного поиска кода
  ├── api.py
  ├── docker-compose.yml
  ├── Dockerfile
  └── requirements.txt
dockerization/        # Файлы для настройки Docker
  └── nginx/
      ├── default.conf
      └── Dockerfile
servers/              # Основной код серверов и агентов
  ├── __init__.py
  ├── function_matcher.py # Скрипт MCP-сервера
  ├── settings.py         # Настройки через pydentic-settings
  ├── websocket.py        # Сервер для подключения к веб-интерфейса
  ├── agentic/            # Работа с агентами
  │   ├── __init__.py
  │   ├── graph_manager.py
  │   ├── llm.py
  │   └── agents/
  │       ├── __init__.py
  │       └── code_wizard/  # Основной агент Code Wizard для поиска по коду
  │           ├── __init__.py
  │           ├── code_wizard.py
  │           └── tools/
  │               ├── __init__.py
  │               ├── code_inspect.py
  │               └── code_search.py
  ├── common/            # Общие модули
  │    ├── __init__.py
  │    ├── mcp_client.py
  │    └── models.py
  └── servers/sourcebot/ # Клиент Sourcebot
       ├── __init__.py
       └── sourcebot_client.py
```

- **code-search-api/**: Содержит API для векторного поиска кода.
- **dockerization/**: Содержит файлы для настройки Docker.
- **servers/**: Содержит основной код серверов и агентов.

## Важные зависимости

... 

## Инструкция по деплою

### Веб вариант (Docker Compose)

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Cоздайте файл `.env` и заполните его, следуя инструкциям в файле
    ```bash
    cp .env.example .env
    ```

2. Соберите и запустите контейнеры:
    ```bash
    docker-compose --env-file .env up --build
    ```

### MCP вариант

...

## Возможные конфигурации

- **.env**: Файл для хранения переменных окружения. Пример конфигурации можно найти в `.env.example`.
- **sourcebot-config.json**: Конфигурационный файл, в котором нужно указывать список репозиториев для поиска.
- **docker-compose.yml**: Файл для настройки и запуска всех сервисов в Docker.
- **requirements.txt**: Список зависимостей Python.
