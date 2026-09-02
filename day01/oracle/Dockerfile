FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# dependencies first: cached until the lockfile changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# then the code, which changes often
COPY app ./app
COPY static ./static
COPY artifacts ./artifacts

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
