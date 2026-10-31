// Credora CI/CD pipeline.
//
// Runs in the Jenkins container of ci/docker-compose.yml, which drives the host
// Docker engine. Build tools run in throwaway containers that share the Jenkins
// workspace volume (--volumes-from), so no host paths are involved.

def COMPOSE = 'docker compose -f docker-compose.yml -f docker-compose.ci.yml'

// Run a script from the repository inside a tool container.
def runIn(String image, String script, String extraArgs = '') {
    sh """
        docker run --rm --volumes-from "\$HOSTNAME" -w "\$WORKSPACE" ${extraArgs} ${image} sh ${script}
    """
}

pipeline {
    agent any

    options {
        skipDefaultCheckout()
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 60, unit: 'MINUTES')
    }

    parameters {
        booleanParam(name: 'SEED_DB', defaultValue: true,
            description: 'Run migrations and seed demo + synthetic data into the database after deploying (idempotent).')
    }

    environment {
        PYTHON_IMAGE  = 'python:3.12-slim'
        NODE_IMAGE    = 'node:22-bookworm-slim'
        SCANNER_IMAGE = 'sonarsource/sonar-scanner-cli:11.4'
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    env.SHORT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.SHORT_SHA}"
                    currentBuild.description = "${env.SHORT_SHA}"
                }
            }
        }

        stage('Prepare') {
            steps {
                withCredentials([file(credentialsId: 'credora-env', variable: 'APP_ENV_FILE')]) {
                    sh 'install -m 600 "$APP_ENV_FILE" .env'
                }
                sh """
                    docker version --format 'Docker engine {{.Server.Version}}'
                    docker compose version
                    ${COMPOSE} config --quiet
                    echo "Image tag: \$IMAGE_TAG"
                """
            }
        }

        stage('Test') {
            parallel {
                stage('Backend tests') {
                    steps {
                        runIn(env.PYTHON_IMAGE, 'ci/scripts/backend-tests.sh', '-v credora-ci-pip-cache:/root/.cache/pip')
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'backend/reports/junit.xml'
                            recordCoverage(
                                tools: [[parser: 'COBERTURA', pattern: 'backend/reports/coverage.xml']],
                                sourceDirectories: [[path: 'backend']],
                                skipPublishingChecks: true
                            )
                        }
                    }
                }
                stage('Frontend checks') {
                    steps {
                        runIn(env.NODE_IMAGE, 'ci/scripts/frontend-checks.sh', '-v credora-ci-npm-cache:/root/.npm')
                    }
                }
            }
        }

        stage('SonarQube analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    runIn(env.SCANNER_IMAGE, 'ci/scripts/sonar-scan.sh',
                        '--user 0 --network credora-ci -e SONAR_HOST_URL -e SONAR_AUTH_TOKEN -e IMAGE_TAG')
                }
            }
        }

        stage('Quality gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build images') {
            steps {
                sh "${COMPOSE} build"
            }
        }

        stage('Deploy') {
            steps {
                sh "${COMPOSE} up -d --remove-orphans --wait --wait-timeout 300"
                sh "${COMPOSE} ps"
            }
        }

        stage('Seed database') {
            when {
                expression { params.SEED_DB }
            }
            steps {
                sh "${COMPOSE} --profile seed run --rm seed"
            }
        }
    }

    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'backend/reports/**'
        }
        failure {
            sh """
                ${COMPOSE} ps -a || true
                for s in \$(${COMPOSE} config --services); do
                    echo "===== \$s ====="
                    ${COMPOSE} logs --no-color --tail 200 "\$s" || true
                done
            """
        }
        cleanup {
            cleanWs()
        }
    }
}
