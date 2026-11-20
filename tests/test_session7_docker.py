from pathlib import Path


def test_session7_dockerfile_and_compose_security() -> None:
    """Session 7 test: verify multi-stage non-root Dockerfile, .dockerignore, and docker-compose.yml."""
    root = Path(__file__).resolve().parent.parent
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (root / ".dockerignore").read_text(encoding="utf-8")
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim AS builder" in dockerfile
    assert "FROM python:3.12-slim AS runtime" in dockerfile
    assert "USER appuser" in dockerfile

    assert ".env" in dockerignore
    assert "*.db" in dockerignore
    assert ".venv" in dockerignore

    assert "postgres:16-alpine" in compose
    assert "redis:7-alpine" in compose
    assert "SECRET_KEY: ${SECRET_KEY:?Set SECRET_KEY in .env}" in compose
