FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --no-dev --script text2sql.py

EXPOSE 2718

CMD ["uv", "run", "text2sql.py", "--host", "0.0.0.0", "--port", "2718"]
