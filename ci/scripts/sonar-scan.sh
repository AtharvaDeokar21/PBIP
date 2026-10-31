#!/bin/sh
# SonarQube analysis of the Python and TypeScript/JavaScript sources.
# Runs in sonarsource/sonar-scanner-cli on the credora-ci network inside
# withSonarQubeEnv('sonarqube'), which provides SONAR_HOST_URL and SONAR_AUTH_TOKEN.
set -eu

sonar-scanner \
  -Dsonar.host.url="${SONAR_HOST_URL}" \
  -Dsonar.token="${SONAR_AUTH_TOKEN}" \
  -Dsonar.projectBaseDir="$(pwd)" \
  -Dsonar.analysis.buildTag="${IMAGE_TAG:-local}"
