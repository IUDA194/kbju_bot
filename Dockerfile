FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# ---- УСТАНАВЛИВАЕМ zbar ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libzbar0 \
    libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- УСТАНОВКА UV ----
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ENV PYTHONPATH=/app

WORKDIR /app
COPY . .

RUN uv sync

CMD ["sh", "-c", "uv run main.py"]

