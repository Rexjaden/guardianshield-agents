{{/*
Expand the name of the chart.
*/}}
{{- define "dhi-vault-csi-provider.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "dhi-vault-csi-provider.fullname" -}}
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
{{- define "dhi-vault-csi-provider.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dhi-vault-csi-provider.labels" -}}
helm.sh/chart: {{ include "dhi-vault-csi-provider.chart" . }}
{{ include "dhi-vault-csi-provider.selectorLabels" . }}
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
{{- define "dhi-vault-csi-provider.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dhi-vault-csi-provider.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "dhi-vault-csi-provider.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "dhi-vault-csi-provider.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate Vault policies for GuardianShield
*/}}
{{- define "dhi-vault-csi-provider.policies" -}}
{{- range $name, $policy := .Values.policies.api }}
# {{ $name | title }} API Policy
path "{{ $policy.path }}" {
  capabilities = {{ $policy.capabilities | toJson }}
}
{{- end }}
{{- end }}

{{/*
Generate Vault roles configuration
*/}}
{{- define "dhi-vault-csi-provider.roles" -}}
{{- range $roleName, $role := .Values.policies.roles }}
# {{ $roleName | title }} Role
bind_service_account_names = ["guardianshield-{{ $roleName }}"]
bind_service_account_namespaces = ["{{ $.Release.Namespace }}"]
policies = {{ $role.policies | toJson }}
ttl = 1h
max_ttl = 24h
{{- end }}
{{- end }}

{{/*
Generate API management configuration
*/}}
{{- define "dhi-vault-csi-provider.apiConfig" -}}
{{- if .Values.apiManagement.enabled }}
# API Management Configuration
api_key_rotation_period = {{ .Values.apiManagement.apiKeys.rotationPeriod }}d
api_key_length = {{ .Values.apiManagement.apiKeys.keyLength }}
jwt_expiration = {{ .Values.apiManagement.jwt.expiration }}s
jwt_issuer = "{{ .Values.apiManagement.jwt.issuer }}"
jwt_audience = "{{ .Values.apiManagement.jwt.audience }}"
{{- end }}
{{- end }}

{{/*
Generate security context
*/}}
{{- define "dhi-vault-csi-provider.securityContext" -}}
{{- toYaml .Values.security.securityContext }}
{{- end }}

{{/*
Generate pod security context
*/}}
{{- define "dhi-vault-csi-provider.podSecurityContext" -}}
{{- toYaml .Values.security.podSecurityContext }}
{{- end }}

{{/*
Generate monitoring labels
*/}}
{{- define "dhi-vault-csi-provider.monitoringLabels" -}}
{{- if .Values.monitoring.enabled }}
app: "guardianshield-vault"
release: "prometheus"
guardianshield.io/monitored: "true"
{{- end }}
{{- end }}

{{/*
Generate Vault address
*/}}
{{- define "dhi-vault-csi-provider.vaultAddress" -}}
{{- if .Values.vault.server.ingress.enabled }}
{{- printf "https://%s" (index .Values.vault.server.ingress.hosts 0).host }}
{{- else }}
{{- printf "https://%s.%s.svc.cluster.local:8200" (include "dhi-vault-csi-provider.fullname" .) .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Validate configuration
*/}}
{{- define "dhi-vault-csi-provider.validateConfig" -}}
{{- if not .Values.global.projectName }}
{{- fail "global.projectName is required" }}
{{- end }}
{{- if and .Values.vault.server.ha.enabled (lt (.Values.vault.server.ha.replicas | int) 3) }}
{{- fail "vault.server.ha.replicas must be at least 3 for HA setup" }}
{{- end }}
{{- if and .Values.apiManagement.enabled (not .Values.apiManagement.jwt.issuer) }}
{{- fail "apiManagement.jwt.issuer is required when API management is enabled" }}
{{- end }}
{{- end }}