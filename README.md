# Sber AI Hackathon 2025

В данном репозитории содержится код бекенда для кейса "Агент Function Matcher", разработанный командой [AllSee.team](https://allSee.team).

## Общая информация

Этот проект представляет собой бэкенд для системы поиска и сопоставления функций в коде. Он включает в себя несколько сервисов, таких как веб-сокеты, API для поиска кода и интеграцию с различными внешними сервисами.

## Структура проекта

- **code-search-api/**: Содержит API для поиска кода.
- **dockerization/**: Содержит файлы для настройки Docker.
- **servers/**: Содержит основной код серверов и агентов.

### Структура репозитория

```
.env.example
.gitignore
docker-compose.yml
Dockerfile
README.md
requirements.txt
sourcebot-config.json
code-search-api/
  ├── api.py
  ├── docker-compose.yml
  ├── Dockerfile
  └── requirements.txt
dockerization/
  └── nginx/
      ├── default.conf
      └── Dockerfile
servers/
  ├── __init__.py
  ├── function_matcher.py
  ├── settings.py
  ├── websocket.py
  ├── agentic/
  │   ├── __init__.py
  │   ├── graph_manager.py
  │   ├── llm.py
  │   └── agents/
  │       ├── __init__.py
  │       ├── code_wizard/
  │       │   ├── __init__.py
  │       │   ├── code_wizard.py
  │       │   └── tools/
  │       │       ├── __init__.py
  │       │       ├── code_inspect.py
  │       │       └── code_search.py
  └── common/
      ├── __init__.py
      ├── mcp_client.py
      └── models.py
servers/sourcebot/
  ├── __init__.py
  └── sourcebot_client.py
```

### Важные программные модули

- **function_matcher.py**: Основной модуль для поиска и сопоставления функций.
- **settings.py**: Модуль для управления настройками и конфигурациями.
- **websocket.py**: Модуль для работы с веб-сокетами.
- **api.py**: Модуль API для поиска кода.
- **graph_manager.py**: Модуль для управления графами.
- **llm.py**: Модуль для работы с языковыми моделями.
- **code_wizard.py**: Модуль агента Code Wizard.
- **mcp_client.py**: Модуль клиента MCP.
- **sourcebot_client.py**: Модуль клиента Sourcebot.

## Инструкция по настройке для локальной разработки

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/your-repo/sber-ai-hack-backend.git
    cd sber-ai-hack-backend
    ```

2. Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Для Windows используйте `venv\Scripts\activate`
    ```

3. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4. Запустите сервер:
    ```bash
    python servers/websocket.py --host=0.0.0.0
    ```

## Инструкция по настройке в Docker

### Веб вариант

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Соберите и запустите контейнеры:
    ```bash
    docker-compose up --build
    ```

### MCP вариант

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Соберите и запустите контейнеры:
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.mcp.yml up --build
    ```

## Возможные конфигурации

- **.env**: Файл для хранения переменных окружения. Пример конфигурации можно найти в `.env.example`.
- **sourcebot-config.json**: Конфигурационный файл для Sourcebot.
- **docker-compose.yml**: Файл для настройки и запуска всех сервисов в Docker.
- **requirements.txt**: Список зависимостей Python.

## Запуск тестов

Для запуска тестов выполните следующую команду:
```bash
pytest
```

## Внесение изменений

1. Создайте новую ветку для ваших изменений:
    ```bash
    git checkout -b feature/my-feature
    ```

2. Внесите изменения и зафиксируйте их:
    ```bash
    git add .
    git commit -m "Добавлено новое изменение"
    ```

3. Отправьте изменения в удаленный репозиторий:
    ```bash
    git push origin feature/my-feature
    ```

4. Создайте Pull Request для ваших изменений.

## Поддержка

Если у вас возникли вопросы или проблемы, пожалуйста, создайте issue в этом репозитории или свяжитесь с командой разработчиков.

## Часто задаваемые вопросы (FAQ)

### Как запустить проект локально?

Следуйте инструкциям в разделе "Инструкция по настройке для локальной разработки".

### Как настроить проект в Docker?

Следуйте инструкциям в разделе "Инструкция по настройке в Docker".

### Как запустить тесты?

Выполните команду `pytest`, как указано в разделе "Запуск тестов".

### Как внести изменения в проект?

Следуйте инструкциям в разделе "Внесение изменений".

### Куда обращаться за поддержкой?

Создайте issue в этом репозитории или свяжитесь с командой разработчиков, как указано в разделе "Поддержка".
