FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv \
 && uv export --frozen --no-dev -o /tmp/requirements.txt \
 && uv pip install --python /opt/venv/bin/python -r /tmp/requirements.txt

COPY src/ /app/src/


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src

RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["/opt/venv/bin/uvicorn", "app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
