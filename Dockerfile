FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--port", "8000"]
