{{/*
Expand the name of the chart.
*/}}
{{- define "dhi-cert-manager.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "dhi-cert-manager.fullname" -}}
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
{{- define "dhi-cert-manager.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dhi-cert-manager.labels" -}}
helm.sh/chart: {{ include "dhi-cert-manager.chart" . }}
{{ include "dhi-cert-manager.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: guardianshield
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dhi-cert-manager.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dhi-cert-manager.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account
*/}}
{{- define "dhi-cert-manager.serviceAccountName" -}}
{{- if .Values.security.serviceAccount.create }}
{{- default (include "dhi-cert-manager.fullname" .) .Values.security.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.security.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate TLS certificate for GuardianShield domains
*/}}
{{- define "dhi-cert-manager.generateDomainCert" -}}
{{- $domains := list -}}
{{- $domains = append $domains .Values.global.domain -}}
{{- $domains = append $domains (printf "www.%s" .Values.global.domain) -}}
{{- $domains = append $domains (printf "api.%s" .Values.global.domain) -}}
{{- $domains = append $domains (printf "admin.%s" .Values.global.domain) -}}
{{- $domains = append $domains (printf "agents.%s" .Values.global.domain) -}}
{{- $domains = append $domains (printf "token.%s" .Values.global.domain) -}}
{{- $domains | join "," -}}
{{- end }}

{{/*
DNS Challenge Solver Configuration
*/}}
{{- define "dhi-cert-manager.dnsChallengeSolver" -}}
{{- if .Values.dnsProviders.cloudflare.enabled }}
- dns01:
    cloudflare:
      email: {{ .Values.dnsProviders.cloudflare.email }}
      apiTokenSecretRef:
        name: cloudflare-api-token
        key: api-token
{{- else if .Values.dnsProviders.route53.enabled }}
- dns01:
    route53:
      region: {{ .Values.dnsProviders.route53.region }}
      accessKeyIDSecretRef:
        name: route53-credentials
        key: access-key-id
      secretAccessKeySecretRef:
        name: route53-credentials
        key: secret-access-key
{{- else if .Values.dnsProviders.googleCloudDNS.enabled }}
- dns01:
    cloudDNS:
      project: {{ .Values.dnsProviders.googleCloudDNS.project }}
      serviceAccountSecretRef:
        name: google-cloud-dns
        key: service-account.json
{{- else }}
- http01:
    ingress:
      class: nginx
{{- end }}
{{- end }}

{{/*
Certificate Monitoring Labels
*/}}
{{- define "dhi-cert-manager.monitoringLabels" -}}
app.kubernetes.io/component: certificate-monitoring
monitoring.guardianshield.io/enabled: "true"
{{- end }}