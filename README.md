# Iris ML Web App - CI/CD Pipeline and Monitoring

ML DevOps Laboratory (UAMPC0732) - Lab ISE-2 - Prathmesh Digvijay Mhopare, Roll No. 56

A Flask web application that predicts the Iris species from four flower measurements,
delivered through a CI/CD pipeline and monitored in production.

| Tool | Role |
|---|---|
| Python + Flask | ML web application (form UI, JSON API, `/health`, `/metrics`) |
| pytest | unit tests, run inside the Docker `test` stage |
| Git + GitHub | version control and source hosting |
| Docker | multi-stage image (test stage + runtime stage) |
| Jenkins | pipeline: checkout -> tests -> build -> deploy -> smoke test -> monitoring check |
| Prometheus | scrapes `/metrics` every 5 s, evaluates alert rules |
| Grafana | dashboard: app status, version, accuracy, traffic, predictions, latency, errors |

## Run locally
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements-dev.txt
    python -m pytest
    python -m app.app            # http://localhost:5000

## Monitoring stack
    docker network create mlops-net
    docker compose -f monitoring/docker-compose.yml up -d
    # Prometheus http://localhost:9090   Grafana http://localhost:3000

## CI/CD
Jenkins pipeline job "iris-mlops-pipeline" -> Pipeline script from SCM -> this repository,
branch `main`, script path `Jenkinsfile`. The Jenkinsfile polls GitHub every 2 minutes;
every push is tested, built, deployed to http://localhost:5000 and smoke-tested.
