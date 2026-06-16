{{/*
Expand the name of the chart.
*/}}
{{- define "aibot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "aibot.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "aibot.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "aibot.labels" -}}
helm.sh/chart: {{ include "aibot.chart" . }}
app.kubernetes.io/name: {{ include "aibot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "aibot.backend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aibot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: backend
{{- end -}}

{{- define "aibot.frontend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aibot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: frontend
{{- end -}}

{{- define "aibot.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- printf "%s/%s:%s" $registry .repo.repository (.repo.tag | default .Chart.AppVersion) -}}
{{- end -}}
