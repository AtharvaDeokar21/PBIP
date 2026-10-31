#!/bin/sh
# Frontend dependency install and TypeScript type check.
# Runs in node:22-bookworm-slim from the repository root (see Jenkinsfile).
set -eu

cd frontend
npm ci --no-audit --no-fund
npm run typecheck
