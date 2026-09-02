# The Oracle: Day 1 app for the DevOps/MLOps course

Date: 2026-09-02
Status: approved

## Context

A two-week course (ten one-hour sessions plus daily take-home assignments) teaching
DevOps and MLOps to machine learning engineers who are weak on cloud. One
application, "the Oracle", is built on Day 1 and every later day adds a DevOps or
MLOps layer to it: containers, CI, cloud deploy, secrets, persistence, model
registry, retraining, observability, orchestration.

Each part of the Day 1 app is chosen to create a cloud problem solved on a later day:

| Day 1 component            | Later lesson it sets up                          |
|----------------------------|--------------------------------------------------|
| LLM API key in env var     | secrets management                               |
| Model artifacts on disk    | artifact storage, model registry, versioning     |
| In-memory chat sessions    | databases, volumes, stateless services           |
| In-memory leaderboard      | databases                                        |
| Agent calls models via HTTP| service splitting, networking, service discovery |
| Committed data CSV         | data versioning                                  |
| Training scripts           | pipelines, scheduled retraining                  |

Day 1 format: the instructor demos and walks through a finished app. Students
receive the full repo. The take-home asks them to run it and extend it.

## Repo layout

The top level of `mlops training/` is a git repository.

```
mlops training/
  README.md                      course overview and proposed 10-day outline
  .gitignore
  docs/superpowers/specs/        design specs
  docs/superpowers/plans/        implementation plans
  day01/
    README.md                    lesson plan for the hour and code walkthrough order
    ASSIGNMENT.md                take-home
    oracle/
      pyproject.toml
      uv.lock
      .python-version            3.12
      .env.example
      Makefile                   install, run, train, test targets
      app/
        __init__.py
        main.py                  FastAPI app factory, mounts static and routers
        config.py                Settings read from env vars
        schemas.py               Pydantic request and response models
        horoscope.py             rule-based horoscope, no ML
        routers/
          chat.py                POST /chat
          predict.py             POST /predict/income, POST /predict/marriage, GET /horoscope
          stats.py               GET /stats, GET /health
        agent/
          graph.py               LangGraph graph construction
          tools.py               the three tools
          persona.py             system prompt
        ml/
          predict.py             loads joblib artifacts, exposes predict functions
          features.py            feature constants shared by training and serving
      static/
        index.html               single page, vanilla JS, no build step
      training/
        prepare_data.py          slims the raw survey CSV to data/so_survey_2025_slim.csv
        train_income.py          trains and saves artifacts/income_model.joblib
        train_marriage.py        generates synthetic data, trains, saves artifacts/marriage_model.joblib
      data/
        so_survey_2025_slim.csv  committed, a few MB
      artifacts/
        income_model.joblib      committed
        marriage_model.joblib    committed
        income_metrics.json      holdout metrics written by training
      tests/
```

The slim CSV and both model artifacts are committed deliberately so students can
run the app without training. The Day 1 README names this as a shortcut that the
model registry day fixes.

## Tooling

- Python 3.12, managed by uv. `uv sync` installs from the lockfile.
- Dependencies: fastapi, uvicorn, pydantic, pydantic-settings, langgraph,
  langchain-openai, langchain-core, scikit-learn, pandas, joblib, httpx,
  python-dotenv. Dev: pytest, pytest-asyncio, ruff.
- Makefile targets: `install`, `run`, `train`, `test`, `lint`.
- `.env.example` documents every variable. `.env` is gitignored.

## Configuration (env vars)

| Variable            | Default                          | Purpose                                  |
|---------------------|----------------------------------|------------------------------------------|
| OPENROUTER_API_KEY  | none, required for /chat         | LLM key                                  |
| LLM_MODEL           | poolside/laguna-s-2.1:free       | OpenRouter model id (changed 2026-09-02 from nvidia/nemotron-3-ultra-550b-a55b:free, which was slow and overloaded) |
| LLM_REASONING       | low                              | reasoning effort for thinking models: off, low, medium, high |
| LLM_MAX_ATTEMPTS    | 3                                | retries per model call for transient provider failures |
| LLM_BASE_URL        | https://openrouter.ai/api/v1     | OpenAI-compatible endpoint               |
| MODEL_API_URL       | http://localhost:8000            | where agent tools find the predict API   |
| ARTIFACTS_DIR       | ./artifacts                      | where joblib files are loaded from       |

Settings are a pydantic-settings class in `config.py`, loaded once. If
OPENROUTER_API_KEY is missing, the app still starts and every non-chat endpoint
works. `POST /chat` returns HTTP 503 with a clear message.

## The agent

A LangGraph `StateGraph` over `MessagesState` with two nodes:

- `agent`: calls the chat model with the three tools bound.
- `tools`: LangGraph's prebuilt `ToolNode`.

Edges: START to agent; conditional edge from agent to tools if the last message has
tool calls, else END; tools back to agent. Compiled with `MemorySaver` so each
`thread_id` (the browser session id) keeps history across requests. Memory is lost
on restart by design.

LLM: `ChatOpenAI` from langchain-openai with `base_url` set to LLM_BASE_URL and
`model` set to LLM_MODEL. Temperature 0.7.

Persona (`persona.py`): a theatrical fortune teller. The system prompt instructs it
to greet, collect the inputs needed for the tools one topic at a time, call the
tools once it has enough, and deliver a dramatic fortune that quotes the tool
results. It must state that the marriage prediction is a joke trained on invented
data and that the income prediction is a statistical estimate from survey data.

Tools (`tools.py`), all async, all using httpx against MODEL_API_URL:

- `get_horoscope(birthday: str)` calls `GET /horoscope?birthday=YYYY-MM-DD`.
- `predict_income(country, years_pro, ed_level, dev_type, remote_work, age_band,
  org_size, languages)` calls `POST /predict/income`.
- `predict_marriage_date(age, relationship_status, coffee_cups_per_day,
  coding_hours_per_week, side_projects, unread_slack_messages)` calls
  `POST /predict/marriage`.

Tools call over HTTP even though Day 1 runs in one process. This makes the agent a
client of the app's own API from the start; splitting services later only changes
MODEL_API_URL.

Risk: the chosen free model may not support tool calling reliably on OpenRouter.
The implementation plan starts with a probe. If it fails, the instructor is told
and LLM_MODEL is changed; nothing else in the design depends on the model.

## The models

### Income predictor

- Data: Stack Overflow Developer Survey 2025, downloaded by `prepare_data.py` from
  `https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/2025/results.csv`
  (141 MB, Git LFS). The script keeps only the needed columns, filters
  `ConvertedCompYearly` to [5000, 500000], and writes the slim CSV. About 22,000 rows.
- Features: Country (top 30 by count, others mapped to "Other"), WorkExp (years of
  professional experience, numeric, capped at 50), EdLevel, DevType (first listed),
  RemoteWork, Age band, OrgSize, and boolean flags for ten languages: Python, SQL,
  JavaScript, TypeScript, Java, C#, C++, Go, Rust, Bash/Shell.
- Target: log of ConvertedCompYearly. Predictions are exponentiated.
- Model: sklearn `Pipeline` of `ColumnTransformer` (OneHotEncoder with
  handle_unknown="ignore" on categoricals, passthrough on numerics and flags) and
  `HistGradientBoostingRegressor`. 80/20 holdout split, random_state fixed.
- Training writes `income_model.joblib` and `income_metrics.json` (MAE in USD,
  median absolute percentage error, n_train, n_test, trained_at, model_version).
- `features.py` holds the category lists and language list so training and serving
  never drift.

### Marriage date predictor

- Data: generated in `train_marriage.py` with a fixed seed. 5,000 rows. Hidden
  formula: years_until_marriage is a function of age, relationship status,
  coffee, coding hours, side projects, and unread Slack messages, plus Gaussian
  noise, clipped to [0.2, 30].
- Model: sklearn `GradientBoostingRegressor` in a Pipeline with one-hot encoding of
  relationship_status.
- Serving converts predicted years into a calendar date from today.
- Every response and the page label it as trained on invented data.

### Horoscope

`horoscope.py` maps a birthday to a zodiac sign and picks one of several templated
messages per sign, seeded by (sign, today's date) so a person gets the same message
all day. No ML.

## API

All request and response bodies are Pydantic models in `schemas.py`.

| Method | Path              | Request                                   | Response                                                    |
|--------|-------------------|-------------------------------------------|-------------------------------------------------------------|
| GET    | /                 |                                           | static/index.html                                           |
| GET    | /health           |                                           | {status, models_loaded, llm_configured}                     |
| POST   | /chat             | {session_id, message}                     | {reply, tools_used: [str]}                                  |
| POST   | /chat/stream      | {session_id, message}                     | text/event-stream: token {text}, tool {name}, error {detail}, done {tools_used} |
| POST   | /predict/income   | IncomeRequest                             | {predicted_income_usd, model_version, disclaimer}           |
| POST   | /predict/marriage | MarriageRequest                           | {predicted_date, years_from_now, model_version, disclaimer} |
| GET    | /horoscope        | ?birthday=YYYY-MM-DD                      | {sign, message}                                             |
| GET    | /stats            |                                           | {fortunes_told, leaderboard: [{name, predicted_income_usd}]} |

Enum fields (ed_level, dev_type, remote_work, age_band, org_size,
relationship_status) are Pydantic `Literal` types built from `features.py`, so the
docs page shows the valid values and bad input gets a 422.

`/predict/income` accepts an optional `name`. When present, the result is added to
the in-memory leaderboard (top 10 by predicted income). Each `/chat` turn that
produces a final answer after tool use increments `fortunes_told`.

Error handling: missing artifacts fail at startup with a clear message telling the
student to run `make train`. LLM errors in `/chat` return 502 with the provider
message. Tool HTTP failures are returned to the LLM as tool error strings so the
Oracle can apologize in character.

## Frontend

`static/index.html`, one file, vanilla JavaScript, fetch calls only.

- Left: chat with the Oracle. Session id generated once per page load and kept in
  `sessionStorage`. Shows which tools were used under each reply.
- Right: two forms hitting `/predict/income` and `/predict/marriage` directly with
  dropdowns populated from the same enums, a horoscope input, and a leaderboard
  plus fortunes-told counter refreshed from `/stats` after each action.
- Light styling, readable on a projector. No framework.

## Testing

pytest with FastAPI `TestClient`.

- Endpoints: health, horoscope (sign mapping, stable message per day), income and
  marriage predict (valid input returns sane range, invalid enum returns 422),
  stats and leaderboard ordering.
- Agent: graph built with a LangChain fake chat model that emits a scripted tool
  call and then a final message, with tools patched to not hit HTTP. Verifies the
  loop and `tools_used`.
- Training: smoke test that `train_income.py` runs on a 200-row sample and writes
  an artifact; `train_marriage.py` runs with a small n.
- Tests never require OPENROUTER_API_KEY or network.

## Lesson material

`day01/README.md`, aimed at ML engineers who have not run servers:

1. Course framing and what the Oracle is (5 min)
2. Live demo of the page (5 min)
3. Concepts: a server process, ports, HTTP request and response, JSON, env vars,
   why a lockfile, what the docs page gives you (10 min)
4. Code walkthrough in this order: `config.py`, `schemas.py`, `routers/predict.py`,
   `ml/predict.py`, `training/train_income.py`, `agent/graph.py`, `agent/tools.py`,
   `routers/chat.py`, `main.py`, `static/index.html` (30 min)
5. The deliberate shortcuts and which day fixes each (5 min)
6. Assignment briefing (5 min)

`day01/ASSIGNMENT.md`:

1. Get an OpenRouter key, run the app with uv, have a full conversation with the
   Oracle, screenshot it.
2. Add one new endpoint and one matching tool of the student's choosing (examples
   given: years until burnout, chance the deploy breaks on Friday), wire it into the
   persona, and write one test for the endpoint.
3. Short written answers: what breaks if two people share a session id, and what
   happens to the leaderboard on restart.

Top-level `README.md`: course goal, audience, how to use the repo, and a proposed
10-day outline (provider-agnostic):

| Day | Topic                                                                    |
|-----|--------------------------------------------------------------------------|
| 1   | The Oracle: FastAPI, a LangGraph agent, and served models, locally       |
| 2   | Containers: Dockerfile, images and layers, docker compose                |
| 3   | CI: GitHub Actions running lint, tests, image build, push to a registry  |
| 4   | Cloud fundamentals: accounts, IAM, regions, first cloud deploy, secrets  |
| 5   | Splitting services and persistence: agent vs model API, Postgres, 12-factor |
| 6   | Model registry and artifact storage: MLflow, object storage, versions    |
| 7   | Training pipelines: scheduled retraining, data versioning                |
| 8   | Observability: structured logs, metrics, dashboards, agent tracing       |
| 9   | Kubernetes basics: deployments, services, config and secrets, scaling    |
| 10  | Model monitoring, drift, rollbacks, canary releases, wrap-up             |

## Out of scope for Day 1

Streaming responses, authentication, a database, Docker, deployment, any cloud
provider setup, and a frontend framework.
