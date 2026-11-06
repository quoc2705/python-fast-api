# TaskHub — Hệ thống quản lý công việc (Task Management API)

Sample application built with **FastAPI**, **Layered Architecture**, **SQLAlchemy 2.x Async**, **Generic Repository Pattern (`BaseRepository[T]`)**, and **Alembic Migrations**.

## Database Schema (8 Core Entities)
1. **`users`**: `id`, `email`, `full_name`, `hashed_password`, `role` (`ADMIN`/`MEMBER`), `is_active`, `created_at`
2. **`workspaces`**: `id`, `name`, `owner_id`, `created_at`
3. **`workspace_members`**: `workspace_id`, `user_id`, `role` (`OWNER`/`EDITOR`/`VIEWER`)
4. **`projects`**: `id`, `workspace_id`, `name`, `description`, `status` (`ACTIVE`/`ARCHIVED`), `created_at`
5. **`tasks`**: `id`, `project_id`, `assignee_id`, `title`, `description`, `status` (`TODO`/`IN_PROGRESS`/`IN_REVIEW`/`DONE`), `priority` (`LOW`/`MEDIUM`/`HIGH`/`URGENT`), `due_date`, `created_by`, `created_at`
6. **`labels`**: `id`, `project_id`, `name`, `color`
7. **`task_labels`**: `task_id`, `label_id`
8. **`comments`**: `id`, `task_id`, `author_id`, `content`, `created_at`

## Quick Start

```powershell
# 1. Run Alembic database migrations
.\.venv\Scripts\alembic upgrade head

# 2. Start the FastAPI server
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

## API Endpoints (`/api/v1`)
- **Users**: `GET /api/v1/users`, `POST /api/v1/users`, `GET /api/v1/users/{id}`, `PATCH /api/v1/users/{id}`, `DELETE /api/v1/users/{id}`
- **Workspaces & Members**:
  - `POST /api/v1/workspaces`, `GET /api/v1/workspaces`, `GET /api/v1/workspaces/{id}`, `PATCH /api/v1/workspaces/{id}`, `DELETE /api/v1/workspaces/{id}`
  - `POST /api/v1/workspaces/{id}/members`, `DELETE /api/v1/workspaces/{id}/members/{user_id}`
  - `POST /api/v1/workspaces/{id}/projects`
- **Projects & Labels**:
  - `GET /api/v1/projects`, `GET /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}`, `POST /api/v1/projects/{id}/archive`, `DELETE /api/v1/projects/{id}`
  - `GET /api/v1/projects/{id}/tasks` (supports filtering by `status`, `priority`, `assignee_id`, `search` + pagination `page` & `limit`)
  - `POST /api/v1/projects/{id}/tasks`
  - `GET /api/v1/projects/{id}/labels`, `POST /api/v1/projects/{id}/labels`, `PATCH /api/v1/projects/{id}/labels/{label_id}`, `DELETE /api/v1/projects/{id}/labels/{label_id}`
- **Tasks, Task Labels & Comments**:
  - `GET /api/v1/tasks`, `GET /api/v1/tasks/{id}`, `PATCH /api/v1/tasks/{id}`, `DELETE /api/v1/tasks/{id}`
  - `POST /api/v1/tasks/{id}/labels/{label_id}`, `DELETE /api/v1/tasks/{id}/labels/{label_id}`
  - `POST /api/v1/tasks/{id}/comments`, `DELETE /api/v1/tasks/{id}/comments/{comment_id}`
