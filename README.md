# Task & Project Management API (FastAPI)

Sample application built with **FastAPI**, **Layered Architecture**, **SQLAlchemy 2.x Async**, **Generic Repository Pattern (`BaseRepository[T]`)**, and **Alembic Migrations**.

## Implemented Modules

### Session 1: Core Setup & Architecture
- **Layered Architecture**:
  - `app/api/` – Routers, request handling, and dependency injection (`Depends`)
  - `app/services/` – Business logic layer (`UserService`, `ProjectService`, `TaskService`)
  - `app/repositories/` – Data access layer (`BaseRepository[T]`, `UserRepository`, `ProjectRepository`, `TaskRepository`)
  - `app/models/` – SQLAlchemy 2.x ORM models (`User`, `Project`, `Task`)
  - `app/schemas/` – Pydantic v2 request/response schemas & generic `PaginatedResponse[T]`
  - `app/core/` & `app/db/` – Configuration and async database session lifecycle (`lifespan`)

### Session 2: Database (SQLAlchemy 2.x & Alembic)
- **SQLAlchemy 2.x Async**: `create_async_engine`, `async_sessionmaker`, `AsyncSession`, `DeclarativeBase`, `Mapped`, and `mapped_column`.
- **Models & Relationships**:
  - `User` (1–N `owned_projects`, 1–N `assigned_tasks`)
  - `Project` (N–1 `owner`, 1–N `tasks` with cascade delete)
  - `Task` (N–1 `project`, N–1 `assignee`)
- **Repository Pattern**: Generic `BaseRepository[ModelType]` supporting async `get_by_id`, `get_multi_paginated`, `create`, `update`, and `delete`.
- **Alembic Migrations**: Async migration setup in `alembic/env.py` and initial migration `0001_initial_schema.py`.

## Quick Start

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
.\.venv\Scripts\pip install -r requirements.txt

# 3. Run Alembic database migrations
.\.venv\Scripts\alembic upgrade head

# 4. Start the FastAPI server
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

## API Endpoints (`/api/v1`)
- **Health**: `GET /health`
- **Users**: `GET /api/v1/users`, `POST /api/v1/users`, `GET /api/v1/users/{user_id}`, `PATCH /api/v1/users/{user_id}`, `DELETE /api/v1/users/{user_id}`
- **Projects**: `GET /api/v1/projects`, `POST /api/v1/projects`, `GET /api/v1/projects/{project_id}`, `PATCH /api/v1/projects/{project_id}`, `DELETE /api/v1/projects/{project_id}`
- **Tasks**: `GET /api/v1/tasks`, `POST /api/v1/tasks`, `GET /api/v1/tasks/{task_id}`, `PUT /api/v1/tasks/{task_id}`, `PATCH /api/v1/tasks/{task_id}`, `DELETE /api/v1/tasks/{task_id}`
- **Interactive Docs**: `http://127.0.0.1:8000/docs`
