{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "eric-oss-pm-solution.fullname" -}}
{{- $name := default .Chart.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- printf "%s" $name }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "eric-oss-pm-solution.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create imagePath.
*/}}
{{- define "eric-oss-pm-solution.imagePath" -}}
{{- $productInfo := fromYaml (.Files.Get "eric-product-info.yaml") -}}
{{- $repoUrl := .Values.image.repoUrl -}}
{{- $repoPath := .Values.image.repoPath -}}
{{- $imageName := $productInfo.images.pm.name -}}
{{- $tag := default .Chart.AppVersion .Values.image.tag -}}
{{- $imagePath := printf "%s/%s/%s:%s" $repoUrl $repoPath $imageName $tag -}}
{{- print (regexReplaceAll "[/]+" $imagePath "/") -}}
{{- end }}

{{/*
Create image pull secret, service level parameter takes precedence
*/}}
{{- define "eric-oss-pm-solution.pullSecret.global" -}}
{{- $pullSecret := "" -}}
{{- if .Values.global -}}
{{- if .Values.global.pullSecret -}}
{{- $pullSecret = .Values.global.pullSecret -}}
{{- end -}}
{{- end -}}
{{- print $pullSecret -}}
{{- end -}}

{{- define "eric-oss-pm-solution.pullSecret" -}}
{{- $pullSecret := ( include "eric-oss-pm-solution.pullSecret.global" . ) -}}
{{- if .Values.imageCredentials.pullSecret -}}
{{- $pullSecret = .Values.imageCredentials.pullSecret -}}
{{- end -}}
{{- print $pullSecret -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "eric-oss-pm-solution.labels" -}}
helm.sh/chart: {{ include "eric-oss-pm-solution.chart" . }}
{{ include "eric-oss-pm-solution.selectorLabels" . }}
{{- if .Chart.Version }}
app.kubernetes.io/version: {{ .Chart.Version | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "eric-oss-pm-solution.selectorLabels" -}}
app: {{ include "eric-oss-pm-solution.fullname" . }}
app.kubernetes.io/name: {{ include "eric-oss-pm-solution.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "eric-oss-pm-solution.loggingLevel" -}}
{{- $loggingLevel := .Values.logging.level | upper -}}
{{- $result := "INFO" -}}
{{- if eq $loggingLevel "DEBUG" -}}
  {{- $result = "DEBUG" -}}
{{- end -}}
{{- print $result -}}
{{- end -}}