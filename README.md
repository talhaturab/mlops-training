# DevOps and MLOps for ML Engineers

A two-week course for machine learning engineers who are comfortable with Python and
models but new to servers, containers, and the cloud. Ten one-hour sessions, one
take-home assignment per day.

## How the course works

- One folder per day: `day01/`, `day02/`, ... Each holds a `README.md` lesson plan, an
  `ASSIGNMENT.md`, and the code for that day.
- One application for the whole course. On Day 1 we build **the Oracle** and run it on a
  laptop. Every later day adds an operations layer to that same app, so by the end you have
  taken one real system from "works on my machine" to "runs in the cloud, monitored,
  retrained on a schedule".

## The Oracle

A FastAPI app with a LangGraph fortune-teller agent. The agent chats with you, collects a
few details, and calls three tools: a rule-based horoscope, a scikit-learn income model
trained on the 2025 Stack Overflow Developer Survey, and a scikit-learn wedding-date model
trained on deliberately invented data. A single HTML page lets you talk to the agent or
hit the models directly, with a class leaderboard of predicted incomes.

## Proposed outline (provider-agnostic)

| Day | Topic |
|---|---|
| 1 | The Oracle: FastAPI, a LangGraph agent, served models, Docker, and a manual EC2 deploy |
| 2 | CI/CD: GitHub Actions runs tests, builds and publishes the image, deploys over SSH |
| 3 | Managed cloud: ECR and App Runner or ECS, throwing the server away |
| 4 | Secrets and configuration: secret managers, IAM, environments |
| 5 | Splitting services and persistence: agent vs model API, Postgres, Compose, 12-factor |
| 6 | Model registry and artifact storage: MLflow, object storage, versions |
| 7 | Training pipelines: scheduled retraining, data versioning |
| 8 | Observability: structured logs, metrics, dashboards, agent tracing |
| 9 | Kubernetes basics: deployments, services, config and secrets, scaling |
| 10 | Model monitoring, drift, rollbacks, canary releases, wrap-up |

This outline is a proposal; later days are adjusted as the class goes.

## Quick start (Day 1)

```bash
cd day01/oracle
cp .env.example .env        # paste your OpenRouter key into .env
make install                # uv sync
make run                    # http://localhost:8000
```

`make test` runs the test suite without needing a key or network access.
A push to `main` runs the pipeline in `.github/workflows/oracle.yml`.
`make probe` checks that your OpenRouter model can call tools.
