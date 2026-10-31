#!/bin/sh
# Backend unit/API tests with JUnit + coverage reports and a Ruff report for SonarQube.
# Runs in python:3.12-slim from the repository root (see Jenkinsfile).
set -eu

export PIP_ROOT_USER_ACTION=ignore
export PIP_DISABLE_PIP_VERSION_CHECK=1

cd backend
pip install --quiet -r requirements.txt pytest-cov==6.2.1

rm -rf reports
mkdir -p reports

ruff check app scripts --output-format=json --exit-zero --output-file reports/ruff.json

pytest -q -p no:cacheprovider \
  --junitxml=reports/junit.xml \
  --cov --cov-report=term --cov-report=xml:reports/coverage.xml
