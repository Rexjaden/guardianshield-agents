FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies and ClamAV
RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    clamav-freshclam \
    clamav-unofficial-sigs \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libmagic1 \
    libmagic-dev \
    libyara10 \
    libyara-dev \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN useradd --create-home --shell /bin/bash clamav-user && \
    mkdir -p /app /app/quarantine /app/temp /app/yara_rules /app/logs && \
    chown -R clamav-user:clamav-user /app

# Install Python dependencies first (for better caching)
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app/
RUN chown -R clamav-user:clamav-user /app

# Copy ClamAV configuration
COPY config/clamd.conf /etc/clamav/clamd.conf
COPY config/freshclam.conf /etc/clamav/freshclam.conf

# Copy YARA rules
COPY yara_rules/*.yar /app/yara_rules/
COPY yara_rules/*.yara /app/yara_rules/

# Create ClamAV directories and set permissions
RUN mkdir -p /var/run/clamav /var/log/clamav /var/lib/clamav && \
    chown -R clamav:clamav /var/run/clamav /var/log/clamav /var/lib/clamav && \
    chmod 755 /var/run/clamav /var/log/clamav

# Download initial virus signatures
RUN freshclam --quiet || echo "Initial signature update failed, will retry at startup"

# Setup systemd-like service management
RUN mkdir -p /etc/supervisor/conf.d
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
COPY config/clamav.conf /etc/supervisor/conf.d/clamav.conf

# Install supervisor
RUN pip3 install supervisor

# Create startup script
COPY scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh && chown clamav-user:clamav-user /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 3310

# Switch to non-root user
USER clamav-user

# Working directory
WORKDIR /app

# Volume for persistent data
VOLUME ["/app/quarantine", "/app/logs", "/var/lib/clamav"]

# Default command
CMD ["/app/start.sh"]