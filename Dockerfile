FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "moodle_mcp.api:app", "--host", "0.0.0.0", "--port", "8000"]
