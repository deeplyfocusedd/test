# Справочник крепёжных изделий

Веб-приложение для поиска крепёжных изделий по параметрам ГОСТа.  
Стек: **Python + FastAPI + Jinja2 + PostgreSQL (JSONB)**.

## Запуск через Docker

```bash
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost:8000

Остановить:
```bash
docker-compose down
```

Остановить и удалить данные БД:
```bash
docker-compose down -v
```

## Запуск локально

Требуется PostgreSQL и Python 3.11.

**1. Создать БД:**
```bash
psql postgres -c "CREATE USER user WITH PASSWORD 'password';"
psql postgres -c "CREATE DATABASE kis OWNER user;"
```

**2. Установить зависимости и запустить:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Структура проекта

```
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py        # FastAPI, маршруты
    ├── database.py    # подключение к PostgreSQL
    ├── init_db.py     # создание таблиц и заполнение данными
    ├── queries.py     # SQL-запросы
    ├── templates/     # HTML-шаблоны (Jinja2)
    └── static/        # CSS
```

## Разделы

| Раздел | URL | Описание |
|--------|-----|----------|
| Каталог | `/` | Поиск КИ по типу, диаметру, длине, ГОСТу |
| ГОСТы | `/gosts` | Список нормативных документов |
| Схема БД | `/schema` | DDL-скрипты таблиц и индексов |
| SQL-запросы | `/queries` | Примеры JSONB-запросов |

## Данные

При первом запуске БД автоматически создаётся и заполняется (~300 записей):

- **ГОСТ 22042-76** — шпильки (d 2–30 мм)
- **ГОСТ 5915-70** — гайки шестигранные (d 3–48 мм)
- **ГОСТ 7798-70** — болты с шестигранной головкой (d 6–30 мм)
- **ГОСТ 1491-80** — шурупы с полукруглой головкой (d 2.5–6 мм)
