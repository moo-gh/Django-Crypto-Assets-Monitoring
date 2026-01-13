# Stage 1: Builder
FROM python:3.12-alpine AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UV_COMPILE_BYTECODE 1
ENV UV_LINK_MODE copy

# Install build dependencies
RUN apk update && \
    apk add --no-cache \
    build-base \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libffi-dev

# Install python dependencies into a virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt


# Stage 2: Final
FROM python:3.12-alpine

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apk add --no-cache \
    libpq \
    jpeg \
    zlib \
    libffi

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy project files
COPY . .

# Set the command
CMD ["gunicorn", "--reload", "--workers=2", "--worker-tmp-dir", "/dev/shm", "--bind=0.0.0.0:80", "--chdir", "/app/crypto_assets", "crypto_assets.wsgi"]
