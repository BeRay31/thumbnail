{{/*
Expand the name of the chart.
*/}}
{{- define "thumbnail-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "thumbnail-service.fullname" -}}
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
{{- define "thumbnail-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "thumbnail-service.labels" -}}
helm.sh/chart: {{ include "thumbnail-service.chart" . }}
{{ include "thumbnail-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "thumbnail-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "thumbnail-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "thumbnail-service.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "thumbnail-service.fullname" .) }}
{{- else }}
{{- .Values.externalPostgresql.host }}
{{- end }}
{{- end }}

{{/*
Redis host
*/}}
{{- define "thumbnail-service.redis.host" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis" (include "thumbnail-service.fullname" .) }}
{{- else }}
{{- .Values.externalRedis.host }}
{{- end }}
{{- end }}

{{/*
MinIO endpoint
*/}}
{{- define "thumbnail-service.minio.endpoint" -}}
{{- if .Values.minio.enabled }}
{{- printf "%s-minio:9000" (include "thumbnail-service.fullname" .) }}
{{- else }}
{{- .Values.externalMinio.endpoint }}
{{- end }}
{{- end }}
