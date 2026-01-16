FROM apache/apisix:3.7.0-debian

# Install required packages for custom plugins
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libpcre3-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create directories for custom plugins and configurations
RUN mkdir -p /usr/local/apisix/apisix/plugins/custom \
             /usr/local/apisix/conf/custom \
             /usr/local/apisix/logs \
             /etc/ssl/apisix

# Copy custom GuardianShield plugins
COPY plugins/guardianshield-*.lua /usr/local/apisix/apisix/plugins/
COPY config/apisix.yaml /usr/local/apisix/conf/config.yaml
COPY routes/ /usr/local/apisix/conf/routes/

# Set proper permissions
RUN chown -R apisix:apisix /usr/local/apisix/apisix/plugins/ \
    && chown -R apisix:apisix /usr/local/apisix/conf/ \
    && chown -R apisix:apisix /usr/local/apisix/logs/ \
    && chmod +x /usr/local/apisix/apisix/plugins/guardianshield-*.lua

# Install Lua dependencies for custom plugins
RUN luarocks install lua-resty-redis \
    && luarocks install lua-resty-http \
    && luarocks install lua-resty-jwt \
    && luarocks install lua-resty-template \
    && luarocks install lua-resty-string

# Create startup script
RUN cat > /usr/local/apisix/bin/start-apisix.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting GuardianShield DHI-APISIX..."

# Wait for etcd to be ready
echo "Waiting for etcd..."
until curl -f http://etcd.guardianshield.svc.cluster.local:2379/health > /dev/null 2>&1; do
    echo "Waiting for etcd to be ready..."
    sleep 2
done
echo "etcd is ready!"

# Initialize APISIX configuration
echo "Initializing APISIX..."
/usr/local/apisix/bin/apisix init

# Load custom routes if available
if [ -d "/usr/local/apisix/conf/routes" ]; then
    echo "Loading custom routes..."
    for route_file in /usr/local/apisix/conf/routes/*.yaml; do
        if [ -f "$route_file" ]; then
            echo "Processing route file: $route_file"
            # Route loading logic would go here
        fi
    done
fi

# Start APISIX
echo "Starting APISIX server..."
exec /usr/local/apisix/bin/apisix start -c /usr/local/apisix/conf/config.yaml
EOF

RUN chmod +x /usr/local/apisix/bin/start-apisix.sh

# Health check script
RUN cat > /usr/local/apisix/bin/health-check.sh << 'EOF'
#!/bin/bash
# Health check for APISIX

# Check if APISIX is responding
if curl -f http://127.0.0.1:9080/apisix/status > /dev/null 2>&1; then
    echo "APISIX is healthy"
    exit 0
else
    echo "APISIX is not responding"
    exit 1
fi
EOF

RUN chmod +x /usr/local/apisix/bin/health-check.sh

# Set environment variables
ENV APISIX_STAND_ALONE=false
ENV APISIX_DEPLOYMENT_ETCD_HOST=http://etcd.guardianshield.svc.cluster.local:2379
ENV APISIX_DEPLOYMENT_ETCD_PREFIX=/apisix
ENV APISIX_DEPLOYMENT_ETCD_TIMEOUT=30

# Security: Run as non-root user
USER apisix

# Expose ports
EXPOSE 9080 9443 9180 9091 9100 9200

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD /usr/local/apisix/bin/health-check.sh

# Volume for logs
VOLUME ["/usr/local/apisix/logs"]

# Set working directory
WORKDIR /usr/local/apisix

# Start APISIX with custom startup script
CMD ["/usr/local/apisix/bin/start-apisix.sh"]

# Metadata labels
LABEL org.opencontainers.image.title="GuardianShield DHI-APISIX"
LABEL org.opencontainers.image.description="Advanced API Security Gateway with GuardianShield threat intelligence"
LABEL org.opencontainers.image.vendor="GuardianShield"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/guardianshield/dhi-apisix"