// CI/CD pipeline for the Iris ML web app (Jenkins on Windows + Docker Desktop)
pipeline {
    agent any

    environment {
        IMAGE   = 'iris-mlops-app'
        APP     = 'iris-app'
        NETWORK = 'mlops-net'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/2 * * * *')          // check GitHub every 2 minutes
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'git log -1 --oneline'
            }
        }

        stage('Tool Check') {
            steps {
                bat 'docker version --format "Docker client {{.Client.Version}} / server {{.Server.Version}}"'
            }
        }

        stage('Unit Tests') {
            steps {
                // builds the 'test' stage of the Dockerfile, which runs pytest
                bat 'docker build --target test -t %IMAGE%:test-%BUILD_NUMBER% .'
            }
        }

        stage('Build Image') {
            steps {
                bat 'docker build --build-arg APP_VERSION=%BUILD_NUMBER% -t %IMAGE%:%BUILD_NUMBER% -t %IMAGE%:latest .'
                bat 'docker images %IMAGE%'
            }
        }

        stage('Deploy') {
            steps {
                bat 'docker network inspect %NETWORK% >nul 2>&1 || docker network create %NETWORK%'
                bat 'docker rm -f %APP% >nul 2>&1 & exit /b 0'
                bat 'docker run -d --name %APP% --network %NETWORK% -p 5000:5000 -e APP_VERSION=%BUILD_NUMBER% --restart unless-stopped %IMAGE%:%BUILD_NUMBER%'
            }
        }

        stage('Smoke Test') {
            steps {
                powershell '''
                    for ($i = 1; $i -le 15; $i++) {
                        try {
                            $h = Invoke-RestMethod http://localhost:5000/health
                            Write-Output "Health: $($h | ConvertTo-Json -Compress)"
                            $body = '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
                            $p = Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/predict -ContentType 'application/json' -Body $body
                            Write-Output "Prediction: $($p | ConvertTo-Json -Compress)"
                            if ($p.species -ne 'setosa') { throw 'wrong prediction' }
                            exit 0
                        } catch { Start-Sleep -Seconds 2 }
                    }
                    Write-Error 'Smoke test failed'; exit 1
                '''
            }
        }

        stage('Monitoring Check') {
            steps {
                powershell '''
                    Start-Sleep -Seconds 12
                    $q = Invoke-RestMethod 'http://localhost:9090/api/v1/query?query=up{job="iris-app"}'
                    $up = $q.data.result[0].value[1]
                    Write-Output "Prometheus: up{job=iris-app} = $up"
                    if ($up -ne '1') { Write-Warning 'Prometheus is not scraping the app yet' }
                '''
            }
        }
    }

    post {
        always {
            bat 'docker rmi %IMAGE%:test-%BUILD_NUMBER% >nul 2>&1 & exit /b 0'
        }
        success {
            echo "Deployed ${env.IMAGE}:${env.BUILD_NUMBER} - http://localhost:5000"
        }
        failure {
            echo 'Pipeline failed - the previous container keeps running only if Deploy was not reached'
        }
    }
}
