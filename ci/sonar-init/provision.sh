#!/bin/sh
# Idempotent SonarQube provisioning for Credora (runs once per `up` of the CI stack):
#   admin password, project, quality gate, new-code definition, Jenkins webhook,
#   and a project analysis token shared with Jenkins through the sonar-secrets volume.
set -eu

SONAR_URL="${SONAR_URL:-http://sonarqube:9000}"
ADMIN_PASSWORD="${SONAR_ADMIN_PASSWORD:-Credora@Sonar1}"
PROJECT_KEY="${SONAR_PROJECT_KEY:-credora}"
PROJECT_NAME="${SONAR_PROJECT_NAME:-Credora}"
QUALITY_GATE="${SONAR_QUALITY_GATE:-Sonar way}"
WEBHOOK_URL="${JENKINS_WEBHOOK_URL:-http://jenkins:8080/sonarqube-webhook/}"
TOKEN_FILE="${TOKEN_FILE:-/secrets/token}"
TOKEN_NAME="jenkins"

log() { echo "[sonar-init] $*"; }
api() { curl -fsS -u "admin:${ADMIN_PASSWORD}" "$@"; }

log "waiting for SonarQube at ${SONAR_URL}"
until curl -fsS "${SONAR_URL}/api/system/status" 2>/dev/null | grep -q '"status":"UP"'; do
  sleep 5
done

# 1. Replace the default admin/admin password.
if curl -fsS -u admin:admin "${SONAR_URL}/api/authentication/validate" | grep -q '"valid":true'; then
  log "changing default admin password"
  curl -fsS -u admin:admin -X POST "${SONAR_URL}/api/users/change_password" \
    --data-urlencode "login=admin" \
    --data-urlencode "previousPassword=admin" \
    --data-urlencode "password=${ADMIN_PASSWORD}"
fi
if ! api "${SONAR_URL}/api/authentication/validate" | grep -q '"valid":true'; then
  log "ERROR: cannot authenticate as admin with SONAR_ADMIN_PASSWORD"
  exit 1
fi

# 2. Project.
if [ "$(api "${SONAR_URL}/api/projects/search?projects=${PROJECT_KEY}" | jq '.paging.total')" = "0" ]; then
  log "creating project ${PROJECT_KEY}"
  api -X POST "${SONAR_URL}/api/projects/create" \
    --data-urlencode "project=${PROJECT_KEY}" \
    --data-urlencode "name=${PROJECT_NAME}" \
    --data-urlencode "mainBranch=main" >/dev/null
fi

# 3. Quality gate.
log "assigning quality gate '${QUALITY_GATE}'"
api -X POST "${SONAR_URL}/api/qualitygates/select" \
  --data-urlencode "gateName=${QUALITY_GATE}" \
  --data-urlencode "projectKey=${PROJECT_KEY}"

# 4. New code = changes since the previous analysed version.
api -X POST "${SONAR_URL}/api/new_code_periods/set" \
  --data-urlencode "project=${PROJECT_KEY}" \
  --data-urlencode "type=PREVIOUS_VERSION"

# 5. Webhook so Jenkins' waitForQualityGate receives the result.
if ! api "${SONAR_URL}/api/webhooks/list" | jq -e --arg url "${WEBHOOK_URL}" '.webhooks[] | select(.url == $url)' >/dev/null; then
  log "creating Jenkins webhook"
  api -X POST "${SONAR_URL}/api/webhooks/create" \
    --data-urlencode "name=Jenkins" \
    --data-urlencode "url=${WEBHOOK_URL}" >/dev/null
fi

# 6. Analysis token (reused while still valid).
if [ -s "${TOKEN_FILE}" ] && curl -fsS -u "$(cat "${TOKEN_FILE}"):" "${SONAR_URL}/api/authentication/validate" | grep -q '"valid":true'; then
  log "existing analysis token is valid"
else
  log "generating analysis token"
  api -X POST "${SONAR_URL}/api/user_tokens/revoke" \
    --data-urlencode "login=admin" --data-urlencode "name=${TOKEN_NAME}" >/dev/null 2>&1 || true
  token="$(api -X POST "${SONAR_URL}/api/user_tokens/generate" \
    --data-urlencode "name=${TOKEN_NAME}" \
    --data-urlencode "type=PROJECT_ANALYSIS_TOKEN" \
    --data-urlencode "projectKey=${PROJECT_KEY}" | jq -r '.token')"
  umask 077
  printf '%s' "${token}" > "${TOKEN_FILE}"
fi

log "done"
