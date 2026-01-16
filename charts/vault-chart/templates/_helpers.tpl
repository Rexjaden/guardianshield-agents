{{/*
Expand the name of the chart.
*/}}
{{- define "vault-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "vault-chart.fullname" -}}
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
{{- define "vault-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "vault-chart.labels" -}}
helm.sh/chart: {{ include "vault-chart.chart" . }}
{{ include "vault-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
guardianshield.io/project: {{ .Values.global.projectName | default "GuardianShield" }}
guardianshield.io/environment: {{ .Values.global.environment | default "production" }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "vault-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "vault-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "vault-chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "vault-chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Vault server labels
*/}}
{{- define "vault-chart.server.labels" -}}
{{ include "vault-chart.labels" . }}
guardianshield.io/component: vault-server
{{- if .Values.vault.server.extraLabels }}
{{- toYaml .Values.vault.server.extraLabels | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Vault server selector labels
*/}}
{{- define "vault-chart.server.selectorLabels" -}}
{{ include "vault-chart.selectorLabels" . }}
component: server
{{- end }}

{{/*
Vault injector labels
*/}}
{{- define "vault-chart.injector.labels" -}}
{{ include "vault-chart.labels" . }}
guardianshield.io/component: vault-injector
{{- if .Values.vault.injector.extraLabels }}
{{- toYaml .Values.vault.injector.extraLabels | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Vault injector selector labels
*/}}
{{- define "vault-chart.injector.selectorLabels" -}}
{{ include "vault-chart.selectorLabels" . }}
component: injector
{{- end }}

{{/*
Create the name of the server service
*/}}
{{- define "vault-chart.server.serviceName" -}}
{{- printf "%s-server" (include "vault-chart.fullname" .) }}
{{- end }}

{{/*
Create the name of the server headless service
*/}}
{{- define "vault-chart.server.headlessServiceName" -}}
{{- printf "%s-server-internal" (include "vault-chart.fullname" .) }}
{{- end }}

{{/*
Create the name of the UI service
*/}}
{{- define "vault-chart.ui.serviceName" -}}
{{- printf "%s-ui" (include "vault-chart.fullname" .) }}
{{- end }}

{{/*
Create vault configuration
*/}}
{{- define "vault-chart.config" -}}
{{- if .Values.vault.server.ha.raft.enabled -}}
{{- .Values.vault.server.ha.raft.config | nindent 0 }}
{{- else if .Values.vault.server.dev.enabled -}}
ui = true
disable_mlock = true
{{- else -}}
ui = {{ .Values.ui.enabled }}
{{- end -}}
{{- end }}

{{/*
Vault image
*/}}
{{- define "vault-chart.server.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.vault.server.image.repository }}
{{- $tag := .Values.vault.server.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" $registry $tag }}
{{- end }}

{{/*
Vault injector image
*/}}
{{- define "vault-chart.injector.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.vault.injector.image.repository }}
{{- $tag := .Values.vault.injector.image.tag }}
{{- printf "%s:%s" $registry $tag }}
{{- end }}

{{/*
Vault agent image
*/}}
{{- define "vault-chart.injector.agentImage" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.vault.injector.agentImage.repository }}
{{- $tag := .Values.vault.injector.agentImage.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" $registry $tag }}
{{- end }}

{{/*
Storage class
*/}}
{{- define "vault-chart.server.storageClass" -}}
{{- if .Values.vault.server.dataStorage.storageClass }}
{{- .Values.vault.server.dataStorage.storageClass }}
{{- else }}
{{- "default" }}
{{- end }}
{{- end }}

{{/*
API Management enabled check
*/}}
{{- define "vault-chart.apiManagement.enabled" -}}
{{- .Values.apiManagement.enabled | default false }}
{{- end }}

{{/*
Monitoring enabled check
*/}}
{{- define "vault-chart.monitoring.enabled" -}}
{{- .Values.monitoring.serviceMonitor.enabled | default false }}
{{- end }}

{{/*
TLS enabled check
*/}}
{{- define "vault-chart.tls.enabled" -}}
{{- not (.Values.global.tlsDisable | default false) }}
{{- end }}

{{/*
External dependencies Redis endpoint
*/}}
{{- define "vault-chart.redis.endpoint" -}}
{{- if .Values.externalDependencies.redis.enabled }}
{{- printf "%s:%d" .Values.externalDependencies.redis.host (.Values.externalDependencies.redis.port | int) }}
{{- else }}
{{- "" }}
{{- end }}
{{- end }}

{{/*
External dependencies PostgreSQL endpoint
*/}}
{{- define "vault-chart.postgresql.endpoint" -}}
{{- if .Values.externalDependencies.postgresql.enabled }}
{{- printf "%s:%d/%s" .Values.externalDependencies.postgresql.host (.Values.externalDependencies.postgresql.port | int) .Values.externalDependencies.postgresql.database }}
{{- else }}
{{- "" }}
{{- end }}
{{- end }}

{{/*
Generate certificates
*/}}
{{- define "vault-chart.gen-certs" -}}
{{- $altNames := list }}
{{- $altNames = append $altNames (printf "%s.%s" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s.%s.svc" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s.%s.svc.cluster.local" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server.%s" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server.%s.svc" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server.%s.svc.cluster.local" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server-internal.%s" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server-internal.%s.svc" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- $altNames = append $altNames (printf "%s-server-internal.%s.svc.cluster.local" (include "vault-chart.fullname" .) .Release.Namespace) }}
{{- if .Values.vault.server.ingress.enabled }}
{{- range .Values.vault.server.ingress.hosts }}
{{- $altNames = append $altNames .host }}
{{- end }}
{{- end }}
{{- $ca := genCA "vault-ca" 365 }}
{{- $cert := genSignedCert (include "vault-chart.fullname" .) nil $altNames 365 $ca }}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
ca.crt: {{ $ca.Cert | b64enc }}
{{- end }}

{{/*
Vault policy template
*/}}
{{- define "vault-chart.policy" -}}
{{- $policyName := .policyName }}
{{- $policyContent := .policyContent }}
{{- printf "path \"%s\" {\n  capabilities = %s\n}" $policyName ($policyContent | toJson) }}
{{- end }}

{{/*
Auth method configuration
*/}}
{{- define "vault-chart.authMethod.config" -}}
{{- $method := .method }}
{{- $config := .config }}
{{- if eq $method "kubernetes" }}
kubernetes_host: {{ $config.kubernetesHost | quote }}
{{- if $config.kubernetesCACert }}
kubernetes_ca_cert: {{ $config.kubernetesCACert | quote }}
{{- end }}
{{- if $config.tokenReviewerJWT }}
token_reviewer_jwt: {{ $config.tokenReviewerJWT | quote }}
{{- end }}
{{- else if eq $method "jwt" }}
jwks_url: {{ $config.jwksURL | quote }}
bound_issuer: {{ $config.boundIssuer | quote }}
default_role: {{ $config.defaultRole | quote }}
{{- end }}
{{- end }}