{{/*
Expand the name of the chart.
*/}}
{{- define "dhi-openresty.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "dhi-openresty.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "dhi-openresty.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dhi-openresty.labels" -}}
helm.sh/chart: {{ include "dhi-openresty.chart" . }}
{{ include "dhi-openresty.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
guardianshield.io/project: {{ .Values.global.projectName }}
guardianshield.io/environment: {{ .Values.global.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dhi-openresty.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dhi-openresty.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "dhi-openresty.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "dhi-openresty.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate upstream servers configuration
*/}}
{{- define "dhi-openresty.upstreams" -}}
{{- range $name, $upstream := .Values.upstreams }}
upstream {{ $name }} {
    {{- if $upstream.loadBalancing }}
    {{ $upstream.loadBalancing }};
    {{- end }}
    
    {{- range $upstream.servers }}
    server {{ .host }}:{{ .port }}{{ if .weight }} weight={{ .weight }}{{ end }}{{ if .maxFails }} max_fails={{ .maxFails }}{{ end }}{{ if .failTimeout }} fail_timeout={{ .failTimeout }}{{ end }};
    {{- end }}
    
    {{- if $upstream.keepalive }}
    keepalive {{ $upstream.keepalive }};
    {{- end }}
}
{{- end }}
{{- end }}

{{/*
Generate SSL certificate paths
*/}}
{{- define "dhi-openresty.sslCertPath" -}}
/etc/ssl/certs/guardianshield/tls.crt
{{- end }}

{{- define "dhi-openresty.sslKeyPath" -}}
/etc/ssl/certs/guardianshield/tls.key
{{- end }}

{{/*
Generate rate limiting configuration
*/}}
{{- define "dhi-openresty.rateLimiting" -}}
{{- if .Values.security.rateLimiting.enabled }}
# Rate limiting zones
{{- range $name, $zone := .Values.security.rateLimiting.zones }}
limit_req_zone {{ $zone.key }} zone={{ $name }}:{{ $zone.size }} rate={{ $zone.rate }};
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate security headers
*/}}
{{- define "dhi-openresty.securityHeaders" -}}
{{- if .Values.security.headers.enabled }}
# Security headers
add_header X-Frame-Options "{{ .Values.security.headers.xFrameOptions }}" always;
add_header X-Content-Type-Options "{{ .Values.security.headers.xContentTypeOptions }}" always;
add_header X-XSS-Protection "{{ .Values.security.headers.xXSSProtection }}" always;
add_header Referrer-Policy "{{ .Values.security.headers.referrerPolicy }}" always;
add_header Strict-Transport-Security "{{ .Values.security.headers.strictTransportSecurity }}" always;
add_header Content-Security-Policy "{{ .Values.security.headers.contentSecurityPolicy }}" always;
{{- end }}
{{- end }}

{{/*
Generate monitoring configuration
*/}}
{{- define "dhi-openresty.monitoring" -}}
{{- if .Values.monitoring.enabled }}
# Nginx status endpoint for monitoring
location /nginx_status {
    stub_status on;
    access_log off;
    
    # Restrict access to monitoring systems
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
}

# Health check endpoint
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}

# Readiness check endpoint
location /ready {
    access_log off;
    
    # Check if upstream services are available
    access_by_lua_block {
        local http = require "resty.http"
        local httpc = http.new()
        
        -- Check backend health
        {{- range $name, $upstream := .Values.upstreams }}
        {{- if $upstream.healthCheck }}
        local res, err = httpc:request_uri("http://{{ (index $upstream.servers 0).host }}:{{ (index $upstream.servers 0).port }}{{ $upstream.healthCheck.path }}")
        if not res or res.status ~= 200 then
            ngx.status = 503
            ngx.say("{{ $name }} backend not ready")
            ngx.exit(503)
        end
        {{- end }}
        {{- end }}
    }
    
    return 200 "ready\n";
    add_header Content-Type text/plain;
}
{{- end }}
{{- end }}

{{/*
Generate Lua script paths
*/}}
{{- define "dhi-openresty.luaScriptPath" -}}
/usr/local/openresty/lualib/guardianshield
{{- end }}

{{/*
Generate log format
*/}}
{{- define "dhi-openresty.logFormat" -}}
log_format main_json escape=json '{'
    '"timestamp":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"request_id":"$request_id",'
    '"remote_user":"$remote_user",'
    '"request":"$request",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"upstream_response_time":"$upstream_response_time",'
    '"upstream_addr":"$upstream_addr",'
    '"http_referrer":"$http_referer",'
    '"http_user_agent":"$http_user_agent",'
    '"http_x_forwarded_for":"$http_x_forwarded_for",'
    '"http_host":"$http_host",'
    '"server_name":"$server_name",'
    '"request_length":$request_length,'
    '"bytes_sent":$bytes_sent,'
    '"gzip_ratio":"$gzip_ratio",'
    '"ssl_protocol":"$ssl_protocol",'
    '"ssl_cipher":"$ssl_cipher"'
'}';
{{- end }}

{{/*
Generate virtual host configuration
*/}}
{{- define "dhi-openresty.virtualHost" -}}
{{- $root := . }}
{{- range $name, $vhost := .Values.virtualHosts }}
# Virtual Host: {{ $name }}
server {
    {{- if $vhost.ssl.enabled }}
    listen 443 ssl http2{{ if $vhost.defaultServer }} default_server{{ end }};
    {{- else }}
    listen 80{{ if $vhost.defaultServer }} default_server{{ end }};
    {{- end }}
    
    server_name {{ join " " $vhost.serverNames }};
    
    {{- if $vhost.ssl.enabled }}
    # SSL Configuration
    ssl_certificate {{ include "dhi-openresty.sslCertPath" $root }};
    ssl_certificate_key {{ include "dhi-openresty.sslKeyPath" $root }};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    {{- end }}
    
    # Access and error logs
    access_log /var/log/nginx/{{ $name }}_access.log main_json;
    error_log /var/log/nginx/{{ $name }}_error.log {{ $vhost.logLevel | default "warn" }};
    
    {{- include "dhi-openresty.securityHeaders" $root | nindent 4 }}
    
    {{- if $root.Values.security.rateLimiting.enabled }}
    # Rate limiting
    {{- range $vhost.rateLimitZones }}
    limit_req zone={{ . }}{{ if $root.Values.security.rateLimiting.burst }} burst={{ $root.Values.security.rateLimiting.burst }}{{ end }}{{ if $root.Values.security.rateLimiting.nodelay }} nodelay{{ end }};
    {{- end }}
    {{- end }}
    
    # Locations
    {{- range $path, $location := $vhost.locations }}
    location {{ $path }} {
        {{- if $location.upstream }}
        proxy_pass http://{{ $location.upstream }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        
        # Timeout configurations
        proxy_connect_timeout {{ $location.timeout.connect | default "60s" }};
        proxy_send_timeout {{ $location.timeout.send | default "60s" }};
        proxy_read_timeout {{ $location.timeout.read | default "60s" }};
        {{- end }}
        
        {{- if $location.auth }}
        # Authentication
        access_by_lua_block {
            local auth = require "guardianshield.auth"
            auth.validate_jwt("{{ $location.auth.secret }}")
        }
        {{- end }}
        
        {{- if $location.cors }}
        # CORS configuration
        header_filter_by_lua_block {
            local cors = require "guardianshield.cors"
            cors.set_headers({
                origin = "{{ $location.cors.origin }}",
                methods = "{{ $location.cors.methods }}",
                headers = "{{ $location.cors.headers }}"
            })
        }
        {{- end }}
        
        {{- if $location.customLua }}
        # Custom Lua logic
        {{- $location.customLua | nindent 8 }}
        {{- end }}
    }
    {{- end }}
}
{{- end }}
{{- end }}

{{/*
Validate configuration
*/}}
{{- define "dhi-openresty.validateConfig" -}}
{{- if not .Values.image.repository }}
{{- fail "image.repository is required" }}
{{- end }}
{{- if not .Values.global.projectName }}
{{- fail "global.projectName is required" }}
{{- end }}
{{- range $name, $vhost := .Values.virtualHosts }}
{{- if not $vhost.serverNames }}
{{- fail (printf "virtualHosts.%s.serverNames is required" $name) }}
{{- end }}
{{- end }}
{{- end }}