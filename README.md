# Sber AI Hackathon 2025

В данном репозитории содержится код бекенда для кейса "Агент Function Matcher", разработанный командой [AllSee.team](https://allSee.team).

## Доступ к прототипу

Воспользоватся прототипом можно через веб-интерфейс по адресу: [http://31.128.49.245/](http://31.128.49.245/)

Также прототип доступен по websocket: [http://31.128.49.245/ws/](http://31.128.49.245/ws/)

Данные необходимо передавать в следующем формате:
```
  {
    "message": "Привет! Проанализируй мой код...",
    "id": "1234",
    "repositories": []
  }
```
Ответ приходит в формате:
```
  {
      "message": "Привет! Я могу помочь с анализом твоей кодовой базы...
      "id": "1234"
  }
```

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

- langgraph
- langchain-core
- mcp
- websockets
- vllm
- sourcebot

## Инструкция по деплою

### Веб вариант (Docker Compose)

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Cоздайте файл `.env` и заполните его, следуя инструкциям в файле
    ```bash
    cp .env.example .env
    ```

3. Соберите и запустите контейнеры фронтенда из репозитария [sber-ai-hack-frontend](https://github.com/allseeteam/sber-ai-hack-frontend)

4. Соберите и запустите контейнеры:
    ```bash
    docker-compose --env-file .env up --build
    ```

### MCP вариант

Mcp сервер доступен в файле `servers/function_matcher.py`.
Его возможно запустить любым удобным mcp клиентом, но предварительно также надо запустить контейнеры из файлa docker-compose (за исключением контейнеров nginx, websocket, frontend) и передать соответствующие переменные окружения.

Пример кода на python:

```
from mcp import ClientSession, StdioServerParameters
from mcp.server.fastmcp import Context
from mcp.client.stdio import stdio_client

from pydantic import BaseModel


class UserRequest(BaseModel):
    message: str
    id: str
    repositories: list[str]


# Параметры подключения к серверу.
server_params = StdioServerParameters(
    command="python",
    args=["servers/function_matcher.py"],
    env={}  # Сюда добавить переменные окружения.
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            ctx = Context()
            result = await session.call_tool(
                name="search_similar_code",
                arguments={
                  "request": UserRequest(
                    id="1234", message="Hi!", repositories=[]
                  ),
                  "ctx": ctx,
                },
            )

            return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())

```


## Возможные конфигурации

- **.env**: Файл для хранения переменных окружения. Пример конфигурации можно найти в `.env.example`.
- **sourcebot-config.json**: Конфигурационный файл, в котором нужно указывать список репозиториев для поиска.
- **docker-compose.yml**: Файл для настройки и запуска всех сервисов в Docker.
- **requirements.txt**: Список зависимостей Python.
