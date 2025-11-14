# Build stage
FROM python:3.14 AS builder

RUN pip install poetry==2.2.1

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml ./
COPY poetry.lock ./
COPY README.md ./

RUN poetry install --only main --no-root

# Runtime stage
FROM python:3.14-slim

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY src/smcb_unlocker ./smcb_unlocker
ENTRYPOINT ["python", "-m", "smcb_unlocker"]
