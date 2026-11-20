# TaskHub — Hệ thống quản lý công việc (Task Management API)

Full-featured Task & Project Management REST API built with **FastAPI**, **Layered Architecture**, **SQLAlchemy 2.x Async**, **Alembic Migrations**, **JWT Authentication**, **RBAC Authorization (`ADMIN`/`OWNER`/`EDITOR`/`VIEWER`)**, **Redis Caching**, **Background Notifications**, and **Docker Compose**.

---

## 1. Architecture & Database Schema (8 Core Entities)

- **Layered Architecture**:
  - `app/api/` — Routers, request validation, and Dependency Injection (`Depends`)
  - `app/services/` — Domain business logic, Unit-of-Work transactions, cache invalidation, and background tasks
  - `app/repositories/` — Generic `BaseRepository[ModelType]` (`flush`-based UoW + pagination) and specialized repositories
  - `app/models/` — SQLAlchemy 2.x Async ORM models (`DeclarativeBase`, `Mapped`, `mapped_column`)
  - `app/schemas/` — Pydantic v2 schemas (`BaseSchema` with whitespace stripping, strict PATCH null guards, generic `PaginatedResponse[T]`)
  - `app/core/` — `pydantic-settings` configuration, JWT/bcrypt security, RBAC guards, Redis cache manager, middlewares, and unified exception handlers

- **8 Database Tables**:
  1. `users`: `id`, `email`, `full_name`, `hashed_password`, `role` (`ADMIN`/`MEMBER`), `is_active`, `created_at`
  2. `workspaces`: `id`, `name`, `owner_id`, `created_at`
  3. `workspace_members`: `workspace_id`, `user_id`, `role` (`OWNER`/`EDITOR`/`VIEWER`)
  4. `projects`: `id`, `workspace_id`, `name`, `description`, `status` (`ACTIVE`/`ARCHIVED`), `created_at`
  5. `tasks`: `id`, `project_id`, `assignee_id`, `title`, `description`, `status` (`TODO`/`IN_PROGRESS`/`IN_REVIEW`/`DONE`), `priority` (`LOW`/`MEDIUM`/`HIGH`/`URGENT`), `due_date`, `created_by`, `created_at`
  6. `labels`: `id`, `project_id`, `name`, `color`
  7. `task_labels`: `task_id`, `label_id`
  8. `comments`: `id`, `task_id`, `author_id`, `content`, `created_at`

---

## 2. Quick Start (Local Development)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
.\.venv\Scripts\pip install -r requirements.txt

# 3. Copy environment configuration and set SECRET_KEY
Copy-Item .env.example .env

# 4. Run Alembic database migrations
.\.venv\Scripts\alembic upgrade head

# 5. Start the FastAPI server
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- **Web Dashboard UI**: `http://127.0.0.1:8000/`
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 3. Running with Docker Compose (`app + db + redis`)

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY (at least 32 characters)
docker compose up --build -d
```

---

## 4. Quality Checks (Tests, Ruff & Mypy)

```powershell
.\.venv\Scripts\pytest -v
.\.venv\Scripts\ruff check app tests
.\.venv\Scripts\mypy app tests
```
