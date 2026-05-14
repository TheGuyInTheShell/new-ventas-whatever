# Stage 1: Build Frontend Assets
FROM node:20-slim AS builder

WORKDIR /app

# Copy dependency files first for caching
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy the rest of the application
COPY . .

# Build the frontend assets using rolldown
RUN npm run build


# Stage 2: Production Python Image
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Caracas \
    MODE=PRODUCTION

# Accept Build ARGs for Coolify compatibility
ARG DB_HOST
ENV DB_HOST=${DB_HOST}
ARG DB_PORT
ENV DB_PORT=${DB_PORT}
ARG DB_USER
ENV DB_USER=${DB_USER}
ARG DB_PASSWORD
ENV DB_PASSWORD=${DB_PASSWORD}
ARG DB_NAME
ENV DB_NAME=${DB_NAME}
ARG DB_DRIVER
ENV DB_DRIVER=${DB_DRIVER}
ARG REDIS_URL
ENV REDIS_URL=${REDIS_URL}
ARG JWT_KEY
ENV JWT_KEY=${JWT_KEY}
ARG JWT_ALG
ENV JWT_ALG=${JWT_ALG}

# Install system dependencies required by python packages and the system
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libpng16-16t64 \
    tzdata \
    && ln -sf /usr/share/zoneinfo/America/Caracas /etc/localtime \
    && echo "America/Caracas" > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv matching local version precisely
RUN pip install --no-cache-dir uv==0.10.7

# Create non-root user with home directory
RUN addgroup --system --gid 1001 pythonapp && \
    adduser --system --uid 1001 pythonapp

# Switch to non-root user
USER pythonapp
WORKDIR /app

# Add virtual environment to PATH and set UV cache directory to a writable path
ENV PATH="/app/.venv/bin:$PATH" \
    UV_CACHE_DIR="/app/.cache/uv"

# Install python dependencies explicitly
COPY --chown=pythonapp:pythonapp pyproject.toml uv.lock ./
RUN uv sync -v --frozen --no-dev

# Copy application source code
COPY --chown=pythonapp:pythonapp . .

# Sync project code
RUN uv sync -v --frozen --no-dev

# Copy built frontend assets from the builder stage
COPY --chown=pythonapp:pythonapp --from=builder /app/src/app/web/out ./src/app/web/out
COPY --chown=pythonapp:pythonapp --from=builder /app/plugins ./plugins

# Make start script executable
RUN chmod +x start.sh

EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0

CMD ["./start.sh"]
