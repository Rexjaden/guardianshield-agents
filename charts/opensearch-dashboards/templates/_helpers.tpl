{{/*
GuardianShield OpenSearch Dashboards Templates
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "dhi-opensearch-dashboards.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "dhi-opensearch-dashboards.fullname" -}}
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
{{- define "dhi-opensearch-dashboards.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dhi-opensearch-dashboards.labels" -}}
helm.sh/chart: {{ include "dhi-opensearch-dashboards.chart" . }}
{{ include "dhi-opensearch-dashboards.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: guardianshield
app.kubernetes.io/component: analytics-dashboard
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dhi-opensearch-dashboards.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dhi-opensearch-dashboards.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "dhi-opensearch-dashboards.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "dhi-opensearch-dashboards.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate certificates for OpenSearch Dashboards
*/}}
{{- define "dhi-opensearch-dashboards.gen-certs" -}}
{{- $altNames := list ( printf "%s.%s" (include "dhi-opensearch-dashboards.fullname" .) .Release.Namespace ) ( printf "%s.%s.svc" (include "dhi-opensearch-dashboards.fullname" .) .Release.Namespace ) -}}
{{- $ca := genCA "guardianshield-dashboards-ca" 365 -}}
{{- $cert := genSignedCert ( include "dhi-opensearch-dashboards.fullname" . ) nil $altNames 365 $ca -}}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
ca.crt: {{ $ca.Cert | b64enc }}
{{- end }}

{{/*
GuardianShield specific configurations
*/}}
{{- define "dhi-opensearch-dashboards.guardianshield-config" -}}
guardianshield.threat_intel.enabled: {{ .Values.guardianshield.analytics.threatIntel.enabled | quote }}
guardianshield.web3.enabled: {{ .Values.guardianshield.analytics.web3.enabled | quote }}
guardianshield.security.enabled: {{ .Values.guardianshield.analytics.security.enabled | quote }}
guardianshield.dmer.integration: {{ .Values.guardianshield.analytics.web3.dmerIntegration | quote }}
{{- end }}