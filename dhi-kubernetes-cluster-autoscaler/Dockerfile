# DHI Kubernetes Cluster Autoscaler for GuardianShield Mining Network
# Docker Hardened Image - Security First
FROM python:3.11-alpine AS builder

# Security: Run as non-root
RUN addgroup -g 1000 guardian && adduser -u 1000 -G guardian -s /bin/sh -D guardian

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.11-alpine

# Security labels
LABEL maintainer="GuardianShield Security <security@guardian-shield.io>"
LABEL org.opencontainers.image.title="DHI Kubernetes Cluster Autoscaler"
LABEL org.opencontainers.image.description="Docker Hardened Image for GuardianShield Mining Node Autoscaling"
LABEL org.opencontainers.image.vendor="GuardianShield"
LABEL org.opencontainers.image.version="1.0.0"
LABEL security.hardened="true"

# Security: Create non-root user
RUN addgroup -g 1000 guardian && adduser -u 1000 -G guardian -s /bin/sh -D guardian

# Install runtime dependencies only
RUN apk add --no-cache \
    curl \
    ca-certificates \
    openssl \
    libffi \
    docker-cli \
    && rm -rf /var/cache/apk/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/guardian/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=guardian:guardian . .

# Security: Set proper permissions
RUN chmod -R 750 /app && \
    chown -R guardian:guardian /app

# Environment variables
ENV PATH=/home/guardian/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV GUARDIAN_AUTOSCALER_VERSION=1.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER guardian

# Expose metrics and API port
EXPOSE 8080

# Start autoscaler
ENTRYPOINT ["python", "-m", "autoscaler"]
CMD ["--config", "/app/config/autoscaler.yaml"]
