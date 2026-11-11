# Busy Yozh

Веб-приложение для управления задачами на Django и Django REST Framework. Поддерживает серверные HTML-страницы и версионированный REST API с JWT-аутентификацией.

## Возможности

- Создание, просмотр, редактирование и удаление задач.
- Назначение и смена исполнителя.
- Отметка задачи выполненной и возврат в работу.
- Комментарии к задачам.
- Регистрация, вход и выход через Django sessions.
- JWT access/refresh для REST API.
- Фильтры и пагинация задач и комментариев.
- OpenAPI-схема, Swagger UI и ReDoc с локальными статическими ресурсами.
- PostgreSQL, Docker Compose, автоматические миграции при запуске разработки.

## Требования

- Docker с поддержкой Docker Compose.
- GNU Make.
- `curl` и `jq` только для примеров API из этого документа.

Локальные Python, Poetry, PostgreSQL и Node.js не нужны.

## Быстрый запуск

```bash
cp .env.example .env
make dev
```

Команда собирает контейнеры, ждёт готовности PostgreSQL, применяет миграции и запускает Django на порту 8000.

Доступные адреса:

- Список задач: <http://localhost:8000/tasks/>
- Регистрация: <http://localhost:8000/accounts/signup/>
- Вход: <http://localhost:8000/accounts/login/>
- Админка: <http://localhost:8000/admin/>
- Swagger UI: <http://localhost:8000/api/docs/swagger/>
- ReDoc: <http://localhost:8000/api/docs/redoc/>
- OpenAPI schema: <http://localhost:8000/api/schema/>
- Health check: <http://localhost:8000/health/>

Для демонстрации зарегистрируйте двух пользователей через HTML. Администратора можно создать отдельно:

```bash
make createsuperuser
```

Остановить сервисы:

```bash
make dev-stop
```

## Архитектура

Проект — модульный Django-монолит. HTML и REST API используют одни сервисы, selectors и правила доступа.

Основные решения:

- `services` выполняют изменения и проверяют права.
- `selectors` содержат чтение, фильтры и оптимизацию запросов.
- `rules` — общие предикаты авторизации для HTML и API.
- HTML использует sessions и CSRF; API использует JWT.
- Изменение статуса принимает явное `is_completed`, поэтому повтор одинакового запроса идемпотентен.

Структура разделена и по техническому слою, и по сущности:

```text
config/                       # Настройки и корневые URL
apps/
├── accounts/
│   ├── models/user.py
│   ├── forms/registration.py
│   ├── views/auth.py
│   └── api/                  # Users API
└── tasks/
    ├── models/               # task.py, comment.py
    ├── services/             # Команды Task и Comment
    ├── selectors/            # QuerySet-функции
    ├── rules/                # Правила доступа
    ├── forms/                # HTML-формы
    ├── views/                # HTML-контроллеры
    ├── api/
    │   ├── serializers/
    │   ├── views/
    │   ├── permissions/
    │   └── urls.py
    └── migrations/
templates/                    # Django Templates
static/css/                   # Локальный CSS, без frontend-сборки
tests/
├── factories/
├── unit/
└── integration/
```

## Команды Makefile

| Команда | Назначение |
|---|---|
| `make help` | Показать справку |
| `make dev` | Собрать и запустить приложение и PostgreSQL |
| `make dev-build` | Собрать образы |
| `make dev-stop` | Остановить сервисы |
| `make dev-clear` | Остановить сервисы и удалить volume БД |
| `make lock` | Пересоздать `poetry.lock` в Docker |
| `make migrate` | Применить миграции |
| `make migration name="change_name"` | Создать миграции |
| `make createsuperuser` | Создать администратора |
| `make shell` | Открыть Django shell |
| `make test` | Запустить все тесты |
| `make test TEST_ARGS="tests/integration/api -v"` | Запустить выбранные тесты |
| `make test-cov` | Тесты и coverage с минимальным порогом 85% |
| `make lint` | Ruff check и проверка форматирования |
| `make format` | Автоисправления Ruff и форматирование |
| `make typecheck` | mypy с django-stubs |
| `make check-django` | Django system check и проверка drift миграций |
| `make check` | Все автоматические проверки |
| `make clean` | Удалить локальные кэши и coverage-файлы |

## REST API

Базовый префикс: `/api/v1/`. Все рабочие endpoints требуют заголовок:

```text
Authorization: Bearer <access-token>
```

| Метод и путь | Действие |
|---|---|
| `POST /auth/token/` | Получить access/refresh |
| `POST /auth/token/refresh/` | Обновить access |
| `GET /users/` | Активные пользователи для назначения |
| `GET, POST /tasks/` | Список и создание задач |
| `GET, PUT, PATCH, DELETE /tasks/{id}/` | Просмотр и изменение задачи |
| `POST /tasks/{task_id}/completion/` | Установить `is_completed` |
| `GET, POST /tasks/{task_id}/comments/` | Список и добавление комментариев |

Список задач поддерживает `author`, `assignee`, `is_completed=true|false` и `page`. Размер страницы — 20. Ответ пагинации содержит `count`, `next`, `previous`, `results`.

### Пример полного сценария

Создайте пользователя через HTML и подставьте его данные и числовой ID исполнителя. Пример использует `jq` для чтения JSON.

```bash
BASE_URL=http://localhost:8000/api/v1
ASSIGNEE_ID=2

TOKEN_RESPONSE=$(curl -sS "$BASE_URL/auth/token/" \
  -H 'Content-Type: application/json' \
  -d '{"username":"your-username","password":"your-password"}')
ACCESS_TOKEN=$(printf '%s' "$TOKEN_RESPONSE" | jq -r '.access')
REFRESH_TOKEN=$(printf '%s' "$TOKEN_RESPONSE" | jq -r '.refresh')

curl -sS "$BASE_URL/auth/token/refresh/" \
  -H 'Content-Type: application/json' \
  -d "{\"refresh\":\"$REFRESH_TOKEN\"}" | jq .

TASK_ID=$(curl -sS "$BASE_URL/tasks/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Подготовить демо","description":"Проверить основной сценарий"}' \
  | jq -r '.id')

curl -sS -X PATCH "$BASE_URL/tasks/$TASK_ID/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"assignee\":$ASSIGNEE_ID}" | jq .

curl -sS "$BASE_URL/tasks/$TASK_ID/completion/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"is_completed":true}' | jq .

curl -sS "$BASE_URL/tasks/$TASK_ID/comments/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Основной сценарий проверен"}' | jq .

curl -sS "$BASE_URL/tasks/?is_completed=true&page=1" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
```

## Правила доступа

| Действие | Аноним | Автор | Исполнитель | Другой аутентифицированный пользователь |
|---|---:|---:|---:|---:|
| Просмотр задач и комментариев | Нет | Да | Да | Да |
| Создание задачи | Нет | Да | Да | Да |
| Редактирование и назначение | Нет | Да | Нет | Нет |
| Удаление задачи | Нет | Да | Нет | Нет |
| Изменение статуса | Нет | Да | Да | Нет |
| Добавление комментария | Нет | Да | Да | Да |

Автор и статус комментария устанавливаются сервером. Через обычный Task endpoint поле `is_completed` доступно только для чтения; используйте `/completion/`.

Коды ошибок: 400 — невалидный ввод, 401 — нет действующей аутентификации, 403 — недостаточно прав, 404 — объект не найден. Анонимный HTML-пользователь перенаправляется на страницу входа.

## Тесты и качество

```bash
make test
make test-cov
make check
```

Тесты запускаются в контейнере против отдельной тестовой PostgreSQL. Покрываются модели, сервисы, selectors, HTML-формы, CSRF, CRUD, JWT, права, пагинация, фильтры и OpenAPI. Минимальный coverage кода `apps` — 85%.

GitHub Actions (`.github/workflows/ci.yml`) собирает Docker-образ и повторяет lint, typecheck, Django checks и тесты с coverage.

## Устранение неполадок

- **Порт 8000 занят:** остановите другое приложение на этом порту или измените mapping `8000:8000` в `docker-compose.yaml`.
- **Нужно начать с чистой БД:** `make dev-clear` удаляет volume и все development-данные, затем выполните `make dev`.
- **Изменились модели:** создайте миграцию через `make migration name="описание"`, проверьте её и примените `make migrate`.
- **Проверка сообщает о новых миграциях:** не редактируйте старые миграции для скрытия drift; создайте новую через Makefile.
- **Нужен интерактивный Django shell:** `make shell`.
