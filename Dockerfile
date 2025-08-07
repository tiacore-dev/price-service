# ===== BASE =====
FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* 


# Указываем переменную
ARG LIB_REPO_TOKEN

ARG CACHE_BUSTER=1
# Чтобы ARG была доступна на этом слое
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install git+https://x-access-token:${LIB_REPO_TOKEN}@github.com/tiacore-dev/tiacore-lib.git@master#${CACHE_BUSTER}



COPY requirements.txt ./


RUN pip install --no-cache-dir -r requirements.txt

# ===== TESTING =====
FROM base AS test   
COPY . .

# ===== FINAL =====
FROM base AS prod
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    ffmpeg \
    libavcodec-extra \
    && update-ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Создаём пользователя и передаём ему владение директорией
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]

