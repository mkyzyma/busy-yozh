# Task Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Dockerized Django task manager with server-rendered HTML, a JWT-protected REST API, comments, permissions, tests, and generated API documentation.

**Architecture:** A modular Django monolith uses one PostgreSQL database and shared application logic for HTML and API. Models, services, selectors, rules, forms, views, serializers, and API permissions are packages split by `User`, `Task`, and `Comment`; controllers stay thin and call the same commands and authorization predicates.

**Tech Stack:** Python 3.12+, Django, Django REST Framework, PostgreSQL, SimpleJWT, drf-spectacular, Poetry, Docker Compose, pytest, pytest-django, factory-boy, Ruff, mypy, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-10-task-management-design.md`

## Global Constraints

- One Django application and one PostgreSQL service; no SPA, microservices, domain-entity mapper, repository layer, or frontend build.
- All routine application, test, migration, lint, and type-check commands run through Docker Compose and the Makefile; local Python is not required.
- Use a custom `accounts.User` from the first migration and PostgreSQL for development and tests.
- HTML uses Django sessions, Forms, Templates, CSRF, and POST for mutations; API uses JWT under `/api/v1/`.
- Only the task author edits, assigns, or deletes a task; author or assignee changes completion; any authenticated user views and comments.
- Split technical packages into files by entity and re-export public models/operations from package `__init__.py` files without circular imports.
- Keep business mutations in services and reads in selectors; serializers and forms validate transport input but do not duplicate business rules.
- Use explicit desired completion state (`is_completed`) rather than an ambiguous toggle operation.
- Pin compatible dependency versions in `pyproject.toml` and `poetry.lock`; do not add dependencies beyond the stated stack without a demonstrated need.
- Ruff, formatting, mypy, Django checks, migration drift checks, and tests must pass; application coverage must be at least 85%.
- Commit messages are one line, with no body or trailers.

## Review Focus

- **Blank, whitespace-only, and oversized text:** task titles and comment bodies must be stripped and rejected without a database write. Pin in Task 3 `test_task_service_rejects_whitespace_title`, Task 4 `test_comment_service_rejects_whitespace_text`, Task 6 `test_create_task_rejects_blank_title`, and Task 7 `test_create_comment_rejects_blank_text`.
- **Direct object access by another user:** changing IDs in URLs or request bodies must not bypass author/assignee rules. Pin in Task 3 service authorization tests, Task 6 `test_other_user_cannot_update_or_delete_task`, Task 7 `test_other_user_cannot_change_completion`, and Tasks 8–9 HTML permission tests.
- **Repeated or unsafe completion requests:** repeating the same desired state is idempotent, and GET never mutates. Pin in Task 3 `test_set_completion_is_idempotent`, Task 7 `test_completion_repeat_returns_current_state`, and Task 9 `test_completion_get_is_not_allowed`.
- **Missing or deleted related users:** assigning a nonexistent user returns validation failure; deleting an assignee leaves the task with `assignee=NULL`. Pin in Task 3 `test_deleting_assignee_keeps_task`, Task 6 `test_assign_nonexistent_user_returns_400`, and Task 5 `test_deleted_user_token_cannot_access_api`.
- **Malformed filters and credentials:** invalid API filter values and invalid JWTs return controlled 400/401 responses, while invalid HTML filters fall back to the default list. Pin in Task 5 `test_invalid_jwt_returns_401`, Task 6 `test_invalid_task_filters_return_400`, and Task 8 `test_invalid_html_filters_show_default_list`.

## File Map

- `manage.py`, `config/`: Django settings, root routing, health endpoint, WSGI/ASGI.
- `apps/accounts/`: custom user, registration/session views, user serializer and list API.
- `apps/tasks/models/`: `task.py`, `comment.py`.
- `apps/tasks/services/`: task and comment commands.
- `apps/tasks/selectors/`: task and comment querysets.
- `apps/tasks/rules/`: task and comment authorization predicates.
- `apps/tasks/forms/`, `apps/tasks/views/`: HTML forms and controllers by entity.
- `apps/tasks/api/`: serializers, views, permissions, and URLs by entity.
- `templates/`, `static/`: authentication and task pages plus local CSS.
- `tests/factories/`: User, Task, and Comment factories.
- `tests/unit/`: models, services, selectors, and rules.
- `tests/integration/`: real Django/DRF HTTP tests against test PostgreSQL.
- `Dockerfile`, `docker/`, `docker-compose*.yaml`, `Makefile`, `.env.example`: reproducible runtime and commands.
- `pyproject.toml`, `poetry.lock`: dependencies, pytest, Ruff, mypy, and coverage configuration.
- `.github/workflows/ci.yml`, `README.md`: CI and user-facing instructions.

---

### Task 1: Project, Docker, and Quality Baseline

**Files:**
- Create: `manage.py`, `config/{__init__,settings,urls,views,wsgi,asgi}.py`
- Create: `pyproject.toml`, `poetry.lock`, `.env.example`, `.gitignore`, `.dockerignore`
- Create: `Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yaml`, `docker-compose.dev.yaml`, `Makefile`
- Test: `tests/integration/test_health.py`

**Interfaces:**
- Consumes: none.
- Produces: `GET /health/` → `200 {"status": "ok"}`; Make targets `dev`, `dev-build`, `dev-stop`, `dev-clear`, `lock`, `test`, `test-cov`, `lint`, `format`, `typecheck`, `check-django`, `check`, `migrate`, `migration name="..."`, `createsuperuser`, `shell`, `clean`.

- [ ] **Step 1: Initialize the repository and dependency/build scaffolding**

Initialize Git if absent. Create a minimal bootable `manage.py`/`config` Django skeleton, including `/admin/`, before writing the health route. Configure Poetry with `package-mode = false`; add Django, DRF, SimpleJWT, drf-spectacular, drf-spectacular-sidecar, psycopg, django-environ, and the development tools listed in the stack. Configure pytest-django, Ruff, mypy django-stubs, and coverage for `apps`. Add safe development values to `.env.example`, never a real secret.

- [ ] **Step 2: Add Docker and Makefile commands**

Use a slim Python image, install Poetry dependencies without creating a second virtual environment, and copy the project. PostgreSQL has a healthcheck and named volume. The development override mounts source and enables autoreload. `docker/entrypoint.sh` runs migrations only when `DJANGO_RUN_MIGRATIONS=1`, then executes the supplied command. Add a `lock` target that runs `poetry lock` inside a Python container with the repository mounted at `/app`, so the initial lock file also requires no local Python.

Define `TEST_ARGS ?= tests` so focused tests run as:

```bash
make test TEST_ARGS="tests/integration/test_health.py -v"
```

The Make target passes `TEST_ARGS` verbatim to pytest.

- [ ] **Step 3: Build the baseline**

Run: `cp .env.example .env && make lock && make dev-build`
Expected: `poetry.lock` is generated in the repository, then images build without dependency resolution errors.

- [ ] **Step 4: Write the failing health test**

```python
def test_health_returns_ok(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 5: Run the test and verify the missing endpoint fails**

Run: `make test TEST_ARGS="tests/integration/test_health.py -v"`
Expected: FAIL with 404 or an unresolved `/health/` route, not an import/configuration error.

- [ ] **Step 6: Complete Django configuration and add the health endpoint**

Complete the settings with environment-driven secret/debug/hosts/database values, installed apps, middleware, templates, static files, DRF defaults, JWT defaults, and PostgreSQL. Add `health_check(request) -> JsonResponse` in `config/views.py` and route `/health/`. Add root `/` as a redirect to the future named URL `task-list` only when that URL exists; until then use `/tasks/` as its literal destination.

- [ ] **Step 7: Verify the baseline**

Run: `make test TEST_ARGS="tests/integration/test_health.py -v" && make lint && make typecheck && make check-django`
Expected: all commands exit 0; health test passes.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: initialize Django project and Docker environment"
```

### Task 2: Custom User and HTML Authentication

**Files:**
- Create: `apps/accounts/{__init__,apps,admin,urls}.py`
- Create: `apps/accounts/models/{__init__,user}.py`, `apps/accounts/forms/{__init__,registration}.py`, `apps/accounts/views/{__init__,auth}.py`
- Create: `apps/accounts/migrations/{__init__,0001_initial}.py`
- Create: `templates/base.html`, `templates/registration/{login,signup}.html`
- Create: `tests/factories/{__init__,accounts}.py`, `tests/unit/accounts/test_user_model.py`
- Test: `tests/integration/accounts/test_html_auth.py`
- Modify: `config/settings.py`, `config/urls.py`, `static/css/app.css`

**Interfaces:**
- Consumes: Task 1 settings, base Docker/test commands.
- Produces: `accounts.User`; `UserFactory`; routes `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/`; settings `AUTH_USER_MODEL="accounts.User"`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`.

- [ ] **Step 1: Write failing user and authentication tests**

Cover the custom model and real HTTP flows with these exact cases:

```python
def test_user_uses_custom_model():
    assert get_user_model().__name__ == "User"
    assert get_user_model()._meta.app_label == "accounts"


def test_signup_creates_user_and_redirects_to_login(client):
    response = client.post("/accounts/signup/", {
        "username": "alice",
        "password1": "Strong-pass-123",
        "password2": "Strong-pass-123",
    })
    assert response.status_code == 302
    assert response.url == "/accounts/login/"
    assert get_user_model().objects.filter(username="alice").exists()
```

Also add `test_login_establishes_session`, `test_logout_requires_post`, `test_logout_clears_session`, and `test_signup_rejects_password_mismatch`; assert respectively authenticated access, 405 for GET logout, cleared `_auth_user_id`, and no created user.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/unit/accounts tests/integration/accounts -v"`
Expected: FAIL because `accounts.User` and authentication routes do not exist.

- [ ] **Step 3: Implement User and registration form**

`User(AbstractUser)` adds no fields and uses the default username behavior. `RegistrationForm(UserCreationForm)` exposes `username`, `password1`, and `password2`. Re-export `User` from `apps/accounts/models/__init__.py`; register it in admin.

- [ ] **Step 4: Implement HTML authentication**

Add signup using `CreateView`/`FormView` with success URL `/accounts/login/`; use Django `LoginView` and `LogoutView`. Logout is POST-only. Add accessible base/login/signup templates, navigation, Django messages, and initial local CSS. Set login/logout redirects to `/tasks/`.

- [ ] **Step 5: Generate and apply the initial user migration**

Run: `make migration name="initial_users" && make migrate`
Expected: migration contains the custom user and applies to PostgreSQL.

- [ ] **Step 6: Add UserFactory**

`UserFactory` produces a unique username and a usable password via `set_password`; no plaintext password is stored on the model. Export it from `tests/factories/__init__.py`.

- [ ] **Step 7: Verify authentication**

Run: `make test TEST_ARGS="tests/unit/accounts tests/integration/accounts -v" && make lint && make typecheck`
Expected: all listed tests pass and checks exit 0.

- [ ] **Step 8: Commit**

```bash
git add apps/accounts config templates static tests pyproject.toml poetry.lock
git commit -m "feat: add custom user and HTML authentication"
```

### Task 3: Task Model, Rules, Services, and Selectors

**Files:**
- Create: `apps/tasks/{__init__,apps,admin,urls}.py`
- Create: `apps/tasks/models/{__init__,task}.py`, `apps/tasks/migrations/{__init__,0001_initial}.py`
- Create: `apps/tasks/rules/{__init__,task}.py`, `apps/tasks/services/{__init__,task}.py`, `apps/tasks/selectors/{__init__,task}.py`
- Create: `tests/factories/tasks.py`
- Test: `tests/unit/tasks/test_task_model.py`, `test_task_rules.py`, `test_task_services.py`, `test_task_selectors.py`

**Interfaces:**
- Consumes: `accounts.User`, `UserFactory`.
- Produces: `Task`; `TaskFactory`; `can_edit_task(*, user: User, task: Task) -> bool`; `can_change_task_completion(*, user: User, task: Task) -> bool`; `create_task(*, author: User, title: str, description: str = "", assignee: User | None = None) -> Task`; `update_task(*, task: Task, actor: User, title: str, description: str = "", assignee: User | None = None) -> Task`; `delete_task(*, task: Task, actor: User) -> None`; `set_task_completion(*, task: Task, actor: User, is_completed: bool) -> Task`; `get_tasks(*, author_id: int | None = None, assignee_id: int | None = None, is_completed: bool | None = None) -> QuerySet[Task]`.

- [ ] **Step 1: Write failing model and service tests**

Use three users (`author`, `assignee`, `other`) and exact assertions for:

- `test_task_defaults_to_incomplete`: a created task has `is_completed is False` and the supplied author.
- `test_task_service_rejects_whitespace_title`: `create_task(..., title="   ")` raises `ValidationError` and `Task.objects.count() == 0`.
- `test_task_title_longer_than_200_is_rejected`: 201 characters raise `ValidationError`.
- `test_only_author_can_update_and_delete`: author succeeds; `other` raises `PermissionDenied` and stored data remains unchanged.
- `test_author_or_assignee_can_complete`: both allowed users can set completion; `other` receives `PermissionDenied`.
- `test_set_completion_is_idempotent`: two calls with `is_completed=True` return the same stored state and do not duplicate anything.
- `test_update_can_assign_and_unassign`: passing a user sets the FK; passing `None` clears it.
- `test_deleting_assignee_keeps_task`: deleting the assigned user leaves the task and sets `assignee_id=None`.
- `test_get_tasks_filters_by_author_assignee_and_status`: each filter returns only matching IDs; combined filters use AND.
- `test_get_tasks_uses_related_users`: list iteration does not issue one query per author/assignee.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/unit/tasks/test_task_model.py tests/unit/tasks/test_task_rules.py tests/unit/tasks/test_task_services.py tests/unit/tasks/test_task_selectors.py -v"`
Expected: FAIL because Task and its operations do not exist.

- [ ] **Step 3: Implement Task and TaskFactory**

Fields: `title=CharField(max_length=200)`, optional text `description`, `author` FK with `related_name="created_tasks"` and CASCADE, nullable `assignee` FK with `related_name="assigned_tasks"` and SET_NULL, indexed boolean `is_completed=False`, timestamps. Strip `title` during model cleaning and reject an empty result. Add ordering by `-created_at` and a readable `__str__`; register Task in Django admin.

- [ ] **Step 4: Implement authorization predicates**

`can_edit_task` requires an authenticated author. `can_change_task_completion` requires an authenticated author or current assignee. Anonymous-like objects and `None` assignees must not cause exceptions.

- [ ] **Step 5: Implement task services and selector**

Services call the appropriate rule before mutation, raise Django `PermissionDenied` on refusal, call `full_clean()`, and save only validated fields. `set_task_completion` updates only `is_completed` and `updated_at`; a repeated value performs no unnecessary UPDATE. `get_tasks` uses `select_related("author", "assignee")` and optional exact filters.

- [ ] **Step 6: Generate migration and verify**

Run: `make migration name="tasks" && make test TEST_ARGS="tests/unit/tasks -v" && make lint && make typecheck`
Expected: migration is created; all task unit tests and quality checks pass.

- [ ] **Step 7: Commit**

```bash
git add apps/tasks tests/factories tests/unit/tasks
git commit -m "feat: add task domain operations"
```

### Task 4: Comment Model, Service, and Selector

**Files:**
- Create: `apps/tasks/models/comment.py`, `apps/tasks/services/comment.py`, `apps/tasks/selectors/comment.py`, `apps/tasks/rules/comment.py`
- Modify: corresponding package `__init__.py` files, `apps/tasks/admin.py`, `tests/factories/tasks.py`
- Create: `apps/tasks/migrations/0002_comment.py`
- Test: `tests/unit/tasks/test_comment_model.py`, `test_comment_services.py`, `test_comment_selectors.py`

**Interfaces:**
- Consumes: `Task`, `User`, factories from Tasks 2–3.
- Produces: `Comment`; `CommentFactory`; `can_comment_task(*, user: User, task: Task) -> bool`; `add_comment(*, task: Task, author: User, text: str) -> Comment`; `get_task_comments(*, task: Task) -> QuerySet[Comment]`.

- [ ] **Step 1: Write failing comment tests**

```python
def test_comment_service_rejects_whitespace_text(task, author):
    with pytest.raises(ValidationError):
        add_comment(task=task, author=author, text="   ")
    assert Comment.objects.count() == 0
```

Add `test_add_comment_sets_author_and_task`, `test_comment_text_longer_than_5000_is_rejected`, `test_any_authenticated_user_can_comment`, `test_comments_are_chronological`, and `test_comment_selector_prefetches_author`. For the last test, create comments by different users and assert no per-comment author queries.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/unit/tasks/test_comment_model.py tests/unit/tasks/test_comment_services.py tests/unit/tasks/test_comment_selectors.py -v"`
Expected: FAIL because Comment and its operations do not exist.

- [ ] **Step 3: Implement Comment and operations**

`Comment` has `task` FK (`related_name="comments"`, CASCADE), `author` FK (`related_name="comments"`, CASCADE), `text=TextField(validators=[MaxLengthValidator(5000)])`, and `created_at`; ordering is `created_at`. Strip text in cleaning and reject blank text. `can_comment_task` requires an authenticated user. `add_comment` checks that rule, calls `full_clean()`, and saves. `get_task_comments` selects the author. Register Comment in Django admin.

- [ ] **Step 4: Migrate and verify**

Run: `make migration name="comment" && make test TEST_ARGS="tests/unit/tasks -v" && make lint && make typecheck`
Expected: all task/comment unit tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/tasks tests/factories tests/unit/tasks
git commit -m "feat: add task comments domain"
```

### Task 5: JWT Authentication and User API

**Files:**
- Create: `apps/accounts/api/{__init__,urls}.py`, `apps/accounts/api/serializers/{__init__,user}.py`, `apps/accounts/api/views/{__init__,user}.py`
- Create: `config/api_urls.py`
- Modify: `config/settings.py`, `config/urls.py`, `tests/factories/accounts.py`
- Test: `tests/integration/api/test_auth.py`, `tests/integration/api/test_users.py`

**Interfaces:**
- Consumes: `accounts.User`, `UserFactory`.
- Produces: `UserSerializer` with only `id` and `username`; `GET /api/v1/users/`; `POST /api/v1/auth/token/`; `POST /api/v1/auth/token/refresh/`; reusable `authenticated_api_client` factory/fixture.

- [ ] **Step 1: Write failing JWT and user-list tests**

Cover:

- `test_token_endpoint_returns_access_and_refresh` for valid credentials and 401 for invalid credentials.
- `test_refresh_endpoint_returns_new_access` and rejects an invalid refresh token with 401.
- `test_api_requires_jwt`: an unauthenticated request to `/api/v1/users/` returns 401.
- `test_valid_jwt_allows_api_access`: `HTTP_AUTHORIZATION="Bearer <access>"` makes the same request return 200.
- `test_invalid_jwt_returns_401`: malformed bearer token returns 401.
- `test_deleted_user_token_cannot_access_api`: issue a token, delete that user, then receive 401.
- `test_user_list_returns_only_public_fields`: authenticated response contains id/username, never password/email/is_staff.
- `test_user_list_excludes_inactive_users` and requires authentication.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/api/test_auth.py tests/integration/api/test_users.py -v"`
Expected: FAIL because versioned API and JWT routes do not exist.

- [ ] **Step 3: Implement versioned API authentication**

Mount `config.api_urls` at `/api/v1/`; include SimpleJWT token routes and account routes. Configure DRF JWT authentication, authenticated-by-default permissions, page-number pagination with size 20, and drf-spectacular schema class. Health, HTML authentication, schema, and docs remain explicit exceptions to JWT-only API access.

- [ ] **Step 4: Implement user list**

`UserListAPIView(ListAPIView)` returns active users ordered by username through `UserSerializer`; no write methods. Add the reusable authenticated APIClient helper without global authentication leakage between tests.

- [ ] **Step 5: Verify API authentication**

Run: `make test TEST_ARGS="tests/integration/api/test_auth.py tests/integration/api/test_users.py -v" && make lint && make typecheck`
Expected: all JWT/user API tests pass; no credentials or private user fields appear in responses.

- [ ] **Step 6: Commit**

```bash
git add apps/accounts config tests
git commit -m "feat: add JWT authentication and user API"
```

### Task 6: Task CRUD and Assignment API

**Files:**
- Create: `apps/tasks/api/{__init__,urls}.py`
- Create: `apps/tasks/api/serializers/{__init__,task}.py`, `apps/tasks/api/views/{__init__,task}.py`, `apps/tasks/api/permissions/{__init__,task}.py`
- Modify: `config/api_urls.py`
- Test: `tests/integration/api/test_task_crud.py`

**Interfaces:**
- Consumes: all Task 3 task interfaces, `UserSerializer`, JWT authentication.
- Produces: `TaskSerializer`, `TaskListQuerySerializer`, `TaskViewSet`, `CanManageTask`; `/api/v1/tasks/` and `/api/v1/tasks/{id}/` supporting GET/POST/PATCH/PUT/DELETE.

- [ ] **Step 1: Write failing task API tests**

Use JWT-authenticated clients for author, assignee, other, and an anonymous client. Cover:

- `test_create_task_uses_token_user_as_author`: POST title/description/assignee returns 201, correct author, default `is_completed=False`.
- `test_create_task_rejects_blank_title` and a 201-character title with 400 and no database row.
- `test_assign_nonexistent_user_returns_400`; no task is created or changed.
- `test_author_cannot_be_changed_through_payload`: response/data retains the original author.
- `test_completion_is_read_only_in_general_task_endpoint`: PATCH with `is_completed` does not change it; clients must use Task 7 completion endpoint.
- `test_task_list_filters_and_paginates`: valid `author`, `assignee`, `is_completed` filters match selector behavior; page size is 20 and response has count/next/previous/results.
- `test_invalid_task_filters_return_400` for non-integer IDs, IDs below 1, and non-boolean completion.
- `test_other_user_cannot_update_or_delete_task`: PATCH/PUT/DELETE return 403 and stored state is unchanged.
- `test_author_can_update_assignee_and_delete_task`: valid updates return 200; delete returns 204 and subsequent GET returns 404.
- `test_anonymous_task_requests_return_401` and missing objects return 404.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/api/test_task_crud.py -v"`
Expected: FAIL with unresolved task routes or 404 responses because task CRUD is not implemented yet.

- [ ] **Step 3: Implement task serializers and permission**

`TaskSerializer` exposes `id,title,description,author,assignee,is_completed,created_at,updated_at`; `author`, `is_completed`, and timestamps are read-only. `assignee` accepts an active User ID or null. Its `create` calls `create_task`; `update` merges partial values and calls `update_task` with `request.user` as actor. `TaskListQuerySerializer` validates positive integer `author`/`assignee` and boolean `is_completed`.

`CanManageTask` allows safe object access to authenticated users and delegates update/delete to `can_edit_task`.

- [ ] **Step 4: Implement TaskViewSet and URLs**

Use `get_tasks()` as the base queryset. Validate list query parameters before applying filters. `perform_create`, `perform_update`, and `perform_destroy` must route through services rather than raw `Model.objects` writes. Return the updated serializer after service calls and use a DRF router with basename `task`.

- [ ] **Step 5: Verify task API**

Run: `make test TEST_ARGS="tests/integration/api/test_task_crud.py tests/unit/tasks -v" && make lint && make typecheck`
Expected: all CRUD/assignment/permission tests pass without regressions.

- [ ] **Step 6: Commit**

```bash
git add apps/tasks config tests/integration/api/test_task_crud.py
git commit -m "feat: add task CRUD API"
```

### Task 7: Completion and Comment API

**Files:**
- Create: `apps/tasks/api/serializers/comment.py`, `apps/tasks/api/views/comment.py`, `apps/tasks/api/views/completion.py`, `apps/tasks/api/permissions/completion.py`
- Modify: API package exports and `apps/tasks/api/urls.py`
- Test: `tests/integration/api/test_task_actions.py`, `tests/integration/api/test_comments.py`

**Interfaces:**
- Consumes: task/comment services and selectors from Tasks 3–4; task API from Task 6.
- Produces: `TaskCompletionSerializer(is_completed: bool)`, `CommentSerializer`, `POST /api/v1/tasks/{task_id}/completion/`, `GET|POST /api/v1/tasks/{task_id}/comments/`.

- [ ] **Step 1: Write failing completion tests**

- `test_author_and_assignee_can_set_completion`: each receives 200 and the requested state.
- `test_other_user_cannot_change_completion`: 403 and unchanged stored state.
- `test_completion_requires_explicit_boolean`: missing or non-boolean `is_completed` returns 400.
- `test_completion_repeat_returns_current_state`: two identical requests both return 200 with the same state.
- `test_completion_does_not_allow_task_field_changes`: extra title/author fields are ignored, the response still reports the requested completion state, and title/author remain unchanged.
- Anonymous receives 401; unknown task returns 404.

- [ ] **Step 2: Write failing comment API tests**

```python
def test_create_comment_uses_token_user(api_client, task):
    response = api_client.post(f"/api/v1/tasks/{task.id}/comments/", {"text": "Looks good"}, format="json")
    assert response.status_code == 201
    assert response.data["author"] == task.author_id
    assert response.data["text"] == "Looks good"
```

Add `test_create_comment_rejects_blank_text`, over-5000 text, `test_comment_list_is_chronological_and_paginated`, `test_comment_author_and_task_are_read_only`, `test_any_authenticated_user_can_comment`, anonymous 401, and missing task 404. Blank/overlength cases assert 400 and no row.

- [ ] **Step 3: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/api/test_task_actions.py tests/integration/api/test_comments.py -v"`
Expected: FAIL because action routes do not exist.

- [ ] **Step 4: Implement completion endpoint**

`TaskCompletionAPIView.post(request, task_id: int) -> Response` retrieves through `get_tasks`, checks `can_change_task_completion` via object permission, validates `TaskCompletionSerializer`, calls `set_task_completion`, and returns `TaskSerializer` with 200.

- [ ] **Step 5: Implement nested comments endpoint**

`CommentListCreateAPIView` resolves the parent task or returns 404. GET uses `get_task_comments`; POST validates `CommentSerializer` and calls `add_comment` with token user and resolved task. Only `id,task,author,text,created_at` are exposed; task/author/timestamp are read-only.

- [ ] **Step 6: Verify action APIs**

Run: `make test TEST_ARGS="tests/integration/api tests/unit/tasks -v" && make lint && make typecheck`
Expected: complete API suite passes.

- [ ] **Step 7: Commit**

```bash
git add apps/tasks/api tests/integration/api
git commit -m "feat: add completion and comment API"
```

### Task 8: HTML Task List and CRUD

**Files:**
- Create: `apps/tasks/forms/{__init__,task}.py`, `apps/tasks/views/{__init__,task}.py`
- Modify: `apps/tasks/urls.py`, `config/urls.py`, `templates/base.html`, `static/css/app.css`
- Create: `templates/tasks/{task_list,task_detail,task_form,task_confirm_delete}.html`, `templates/tasks/includes/task_card.html`
- Test: `tests/integration/html/test_task_crud.py`

**Interfaces:**
- Consumes: task services/selectors/rules and session authentication.
- Produces: named routes `task-list`, `task-create`, `task-detail`, `task-update`, `task-delete`; `TaskForm`; HTML list filters `scope=all|mine|assigned` and `status=all|active|completed`.

- [ ] **Step 1: Write failing HTML CRUD tests**

Use Django `Client` with logged-in author/other users and assert:

- `test_task_pages_require_login`: anonymous users are redirected to login with `next`.
- `test_create_task`: valid POST redirects to detail, uses session user as author, and persists assignee.
- `test_create_task_invalid_form_rerenders`: blank title returns 200 with form errors and no task.
- `test_task_list_scope_and_status_filters`: all/mine/assigned and active/completed show exactly expected task IDs in context.
- `test_invalid_html_filters_show_default_list`: unknown scope/status values fall back to all tasks rather than raising or filtering everything out.
- `test_task_list_paginates_by_20` and detail displays author/assignee/status.
- `test_author_can_edit_and_unassign_task`: valid POST redirects and updates values.
- `test_other_user_cannot_edit_or_delete_task`: GET/POST return 403 and data remains unchanged.
- `test_delete_requires_post_and_confirmation`: GET shows confirmation without deleting; POST deletes and redirects to list.
- Missing task returns 404.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/html/test_task_crud.py -v"`
Expected: FAIL because task HTML routes/templates do not exist.

- [ ] **Step 3: Implement TaskForm and list/detail views**

`TaskForm(ModelForm)` exposes title, description, and active assignee choices ordered by username. List view uses `get_tasks`, explicit filter mapping, 20-item pagination, and related-user eager loading. Detail uses `get_task_comments` and exposes rule results for action buttons.

- [ ] **Step 4: Implement create/update/delete controllers**

Controllers call Task 3 services after form validation. Authenticated non-authors receive `PermissionDenied`/403 rather than login redirect. Update uses the existing object; delete performs no work on GET. Successful mutations use Post/Redirect/Get and Django messages.

- [ ] **Step 5: Implement usable templates and CSS**

Extend the base template, display validation/non-field errors, render filters and pagination, and only show permitted action controls. Keep all assets local and all state-changing controls as POST forms with CSRF tokens.

- [ ] **Step 6: Verify HTML CRUD**

Run: `make test TEST_ARGS="tests/integration/html/test_task_crud.py tests/unit/tasks -v" && make lint && make typecheck`
Expected: all HTML CRUD tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/tasks config templates static tests/integration/html
git commit -m "feat: add HTML task management"
```

### Task 9: HTML Completion and Comments

**Files:**
- Create: `apps/tasks/forms/comment.py`, `apps/tasks/views/comment.py`, `apps/tasks/views/completion.py`
- Modify: task view exports, `apps/tasks/urls.py`, `templates/tasks/task_detail.html`, `static/css/app.css`
- Test: `tests/integration/html/test_task_actions.py`

**Interfaces:**
- Consumes: Task 4 comments, Task 3 completion/rules, Task 8 detail template.
- Produces: `CommentForm`; named POST routes `task-completion` and `comment-create`.

- [ ] **Step 1: Write failing HTML action tests**

- `test_author_and_assignee_can_complete_and_reopen`: POST desired boolean strings and assert redirect plus stored state.
- `test_other_user_cannot_change_completion`: 403 and unchanged state.
- `test_completion_get_is_not_allowed`: GET returns 405 and does not mutate.
- `test_completion_requires_valid_boolean`: absent/invalid value returns 400 without mutation.
- `test_user_can_add_comment`: POST redirects to detail and stores current user as author.
- `test_blank_comment_rerenders_detail_with_errors`: status 400, errors visible, no row.
- `test_comment_get_is_not_allowed`: 405 and no row.
- `test_comment_list_is_visible_on_detail` in chronological order.
- `test_mutating_html_forms_require_csrf`: with `Client(enforce_csrf_checks=True)`, a POST without token receives 403 and does not mutate.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/html/test_task_actions.py -v"`
Expected: FAIL because action routes do not exist.

- [ ] **Step 3: Implement completion and comment controllers**

Completion accepts only POST, parses an explicit `true`/`false` value, checks `can_change_task_completion`, and calls `set_task_completion`. Comment accepts only POST, checks `can_comment_task`, and calls `add_comment`. Invalid comment input rerenders detail with task, comments, and form errors at status 400.

- [ ] **Step 4: Add detail-page actions**

Render completion/reopen button with the opposite desired state, chronological comments, and comment form. Hide forbidden completion controls while retaining server-side enforcement.

- [ ] **Step 5: Verify all HTML behavior**

Run: `make test TEST_ARGS="tests/integration/html tests/integration/accounts -v" && make lint && make typecheck`
Expected: HTML suite passes, including CSRF and method restrictions.

- [ ] **Step 6: Commit**

```bash
git add apps/tasks templates static tests/integration/html
git commit -m "feat: add HTML completion and comments"
```

### Task 10: OpenAPI, Swagger, and ReDoc

**Files:**
- Modify: `config/settings.py`, `config/urls.py`, `pyproject.toml`, `poetry.lock`
- Test: `tests/integration/test_openapi.py`

**Interfaces:**
- Consumes: complete versioned API from Tasks 5–7 and drf-spectacular dependencies.
- Produces: public `GET /api/schema/`, `GET /api/docs/swagger/`, `GET /api/docs/redoc/`; locally served documentation assets.

- [ ] **Step 1: Write failing documentation tests**

- `test_openapi_schema_is_public_and_valid`: anonymous GET returns 200 and OpenAPI content with `openapi` and `paths`.
- `test_schema_contains_versioned_task_operations`: paths include task CRUD, completion, comments, users, token, and refresh.
- `test_task_schema_documents_author_and_completion_rules`: descriptions/extensions explicitly state that author is server-assigned and completion uses the dedicated endpoint.
- `test_swagger_and_redoc_are_available`: both return 200 and their expected HTML markers.
- `test_docs_assets_are_local`: rendered documentation references the installed sidecar static assets, not a third-party CDN.

- [ ] **Step 2: Run tests and verify failure**

Run: `make test TEST_ARGS="tests/integration/test_openapi.py -v"`
Expected: FAIL because documentation routes/configuration are absent or incomplete.

- [ ] **Step 3: Configure schema and documentation**

Set API title `Task Manager API`, version `1.0.0`, a concise description of JWT and permissions, and `SERVE_PERMISSIONS=["rest_framework.permissions.AllowAny"]`. Add drf-spectacular-sidecar static configuration, schema/Swagger/ReDoc routes, and serializer/view docstrings only where they clarify request fields, permissions, or response behavior.

- [ ] **Step 4: Verify documentation and full API schema generation**

Run: `make test TEST_ARGS="tests/integration/test_openapi.py tests/integration/api -v" && make check-django`
Expected: tests pass and schema generation has no errors that hide endpoints.

- [ ] **Step 5: Commit**

```bash
git add config apps pyproject.toml poetry.lock tests/integration/test_openapi.py
git commit -m "docs: add OpenAPI Swagger and ReDoc"
```

### Task 11: Documentation, CI, and Release Verification

**Files:**
- Create: `README.md`, `.github/workflows/ci.yml`
- Modify as needed: `Makefile`, `.env.example`, `pyproject.toml`, `poetry.lock`
- Test: full suite plus real-container smoke verification; no test-only production branches.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: reproducible setup/test instructions, endpoint/permission documentation, CI quality gate, and a repository ready to publish.

- [ ] **Step 1: Write README as executable instructions**

Document features, architecture rationale, entity-split file structure, requirements, `.env` setup, all Make targets, user creation, HTML URLs, JWT flow, endpoint table, permission matrix, filtering/pagination, Swagger/ReDoc, tests, coverage, and troubleshooting. Include curl examples for token → create → assign → complete → comment → list; do not place real credentials in examples.

- [ ] **Step 2: Add CI**

GitHub Actions checks out the repository, copies `.env.example`, builds Compose images, then runs `make lint`, `make typecheck`, `make check-django`, and `make test-cov`. Cache only reproducible dependency/build data; do not cache `.env`, database data, or coverage artifacts.

- [ ] **Step 3: Run focused and complete automated verification**

Run:

```bash
make lint
make format
make lint
make typecheck
make check-django
make test-cov
make dev-build
```

Expected: formatting leaves no subsequent lint changes, all tests pass against PostgreSQL, coverage is at least 85%, and Docker build succeeds. Inspect `git status` afterward and remove only generated caches/reports not intended for the repository.

- [ ] **Step 4: Verify the actual running application**

Start with `make dev`; run `curl --fail http://localhost:8000/health/` and confirm `{"status":"ok"}`. In the browser, register two users and execute the original scenario through HTML: user A creates and assigns a task to B; B completes it and comments; A edits/reopens it; a third user cannot edit/delete it; A deletes it. Repeat create/assign/complete/comment/list through Swagger using JWT and verify 401/403/400 cases. Check `/api/docs/redoc/`.

Stop with `make dev-stop`; no manual database changes may be needed for this workflow.

- [ ] **Step 5: Review repository contents and documentation accuracy**

Confirm README commands and URLs match the implementation, `.env` and local data are ignored, migrations are present, no generated caches or secrets are tracked, and `git diff --check` reports no whitespace errors. Do not fix unrelated issues or publish to GitHub without the user's repository/remote approval.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "docs: add setup instructions and CI verification"
```

## Final Acceptance Criteria

- All required operations work in both HTML and REST API with the same permissions.
- JWT access/refresh, Swagger, and ReDoc work.
- `make dev` starts the complete application with PostgreSQL and migrations.
- `make check` and `make test-cov` pass, with application coverage at least 85%.
- README enables a reviewer to run and exercise the project using Docker alone.
- The repository contains source, focused entity files, migrations, tests, lock file, Docker/Compose, Makefile, CI, and no local secrets/artifacts.
