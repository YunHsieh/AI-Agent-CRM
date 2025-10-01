FROM python:3.12-slim

WORKDIR /ai-agent-crm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Poetry
RUN pip install poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root

COPY . .

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /ai-agent-crm

USER appuser

EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# 啟動命令
CMD ["python", "main.py"]
