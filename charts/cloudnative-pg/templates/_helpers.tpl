{{/*
Expand the name of the chart.
*/}}
{{- define "dhi-cloudnative-pg.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "dhi-cloudnative-pg.fullname" -}}
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
{{- define "dhi-cloudnative-pg.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dhi-cloudnative-pg.labels" -}}
helm.sh/chart: {{ include "dhi-cloudnative-pg.chart" . }}
{{ include "dhi-cloudnative-pg.selectorLabels" . }}
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
{{- define "dhi-cloudnative-pg.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dhi-cloudnative-pg.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Database connection string template
*/}}
{{- define "dhi-cloudnative-pg.connectionString" -}}
{{- printf "postgresql://%s:%s@%s-rw.%s.svc.cluster.local:5432/%s" .Values.initdb.owner "${DATABASE_PASSWORD}" .Values.cluster.name .Release.Namespace .Values.initdb.database }}
{{- end }}

{{/*
Pooler connection string template
*/}}
{{- define "dhi-cloudnative-pg.poolerConnectionString" -}}
{{- if .Values.pooler.enabled }}
{{- printf "postgresql://%s:%s@%s-pooler-rw.%s.svc.cluster.local:5432/%s" .Values.initdb.owner "${DATABASE_PASSWORD}" .Values.cluster.name .Release.Namespace .Values.initdb.database }}
{{- else }}
{{- include "dhi-cloudnative-pg.connectionString" . }}
{{- end }}
{{- end }}

{{/*
Generate database credentials secret name
*/}}
{{- define "dhi-cloudnative-pg.secretName" -}}
{{- default (printf "%s-credentials" .Values.cluster.name) .Values.initdb.secret }}
{{- end }}

{{/*
Generate backup S3 credentials secret name
*/}}
{{- define "dhi-cloudnative-pg.backupSecretName" -}}
{{- if .Values.backup.enabled }}
{{- printf "%s-backup-s3-credentials" .Values.cluster.name }}
{{- end }}
{{- end }}

{{/*
Generate monitoring labels
*/}}
{{- define "dhi-cloudnative-pg.monitoringLabels" -}}
{{- if .Values.monitoring.enabled }}
app: "guardianshield-postgres"
release: "prometheus"
guardianshield.io/monitored: "true"
{{- end }}
{{- end }}

{{/*
Generate network policy name
*/}}
{{- define "dhi-cloudnative-pg.networkPolicyName" -}}
{{- printf "%s-network-policy" .Values.cluster.name }}
{{- end }}

{{/*
Generate service names
*/}}
{{- define "dhi-cloudnative-pg.serviceName.rw" -}}
{{- printf "%s-rw" .Values.cluster.name }}
{{- end }}

{{- define "dhi-cloudnative-pg.serviceName.ro" -}}
{{- printf "%s-ro" .Values.cluster.name }}
{{- end }}

{{- define "dhi-cloudnative-pg.serviceName.pooler" -}}
{{- if .Values.pooler.enabled }}
{{- printf "%s-pooler-rw" .Values.cluster.name }}
{{- end }}
{{- end }}

{{/*
Generate backup job name
*/}}
{{- define "dhi-cloudnative-pg.backupJobName" -}}
{{- if .Values.backup.enabled }}
{{- printf "%s-backup" .Values.cluster.name }}
{{- end }}
{{- end }}

{{/*
Generate resource quotas
*/}}
{{- define "dhi-cloudnative-pg.resourceQuotas" -}}
requests.cpu: {{ .Values.resources.requests.cpu | quote }}
requests.memory: {{ .Values.resources.requests.memory | quote }}
limits.cpu: {{ .Values.resources.limits.cpu | quote }}
limits.memory: {{ .Values.resources.limits.memory | quote }}
{{- end }}

{{/*
Generate security context with defaults
*/}}
{{- define "dhi-cloudnative-pg.securityContext" -}}
{{- $defaultSecurityContext := dict "runAsNonRoot" true "runAsUser" 999 "runAsGroup" 999 "fsGroup" 999 "allowPrivilegeEscalation" false }}
{{- toYaml (merge .Values.security.securityContext $defaultSecurityContext) }}
{{- end }}

{{/*
Generate pod security context with defaults
*/}}
{{- define "dhi-cloudnative-pg.podSecurityContext" -}}
{{- $defaultPodSecurityContext := dict "runAsNonRoot" true "runAsUser" 999 "runAsGroup" 999 "fsGroup" 999 }}
{{- toYaml (merge .Values.security.podSecurityContext $defaultPodSecurityContext) }}
{{- end }}

{{/*
Generate database configuration checksum
*/}}
{{- define "dhi-cloudnative-pg.configChecksum" -}}
{{- include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
{{- end }}

{{/*
Generate PostgreSQL extensions list
*/}}
{{- define "dhi-cloudnative-pg.extensions" -}}
{{- if .Values.extensions }}
{{- range .Values.extensions }}
- {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate database initialization scripts
*/}}
{{- define "dhi-cloudnative-pg.initScripts" -}}
{{- if .Values.initdb.databases }}
{{- range .Values.initdb.databases }}
CREATE DATABASE IF NOT EXISTS {{ .name }};
{{- if .owner }}
ALTER DATABASE {{ .name }} OWNER TO {{ .owner }};
{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Validate required values
*/}}
{{- define "dhi-cloudnative-pg.validateConfig" -}}
{{- if not .Values.cluster.name }}
{{- fail "cluster.name is required" }}
{{- end }}
{{- if not .Values.initdb.database }}
{{- fail "initdb.database is required" }}
{{- end }}
{{- if not .Values.initdb.owner }}
{{- fail "initdb.owner is required" }}
{{- end }}
{{- if and .Values.backup.enabled (not .Values.backup.s3.bucket) }}
{{- fail "backup.s3.bucket is required when backup is enabled" }}
{{- end }}
{{- end }}