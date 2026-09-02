# Day 1: The Oracle

**Goal for the hour:** run one real service on your laptop, understand every piece of it,
and see why each piece will become a cloud problem in the days that follow.

Everything lives in `day01/oracle/`. Start the app with `make run` and open
http://localhost:8000.

## 1. What we build today and why (5 min)

The Oracle is a FastAPI app with three parts:

- **An agent** (LangGraph) that plays a fortune teller and calls tools.
- **Two served models** (scikit-learn): an income predictor trained on the 2025 Stack
  Overflow Developer Survey, and a wedding-date predictor trained on invented data.
- **A web page** that talks to both.

We are not building it because the world needs a fortune teller. We are building it because
each part creates a problem you only meet once software leaves your laptop:

| Day 1 component | Later lesson it sets up |
|---|---|
| LLM API key in an env var | secrets management |
| Model artifacts on disk | artifact storage, model registry, versioning |
| In-memory chat sessions | databases, volumes, stateless services |
| In-memory leaderboard | databases |
| Agent calls models over HTTP | service splitting, networking, service discovery |
| Committed data CSV | data versioning |
| Training scripts | pipelines, scheduled retraining |

## 2. Demo (5 min)

1. Open the page. Chat with the Oracle until all three tools have fired. Watch the
   "tools used" line under each reply.
2. Use the forms on the right to hit the models directly. Put your name in and watch the
   leaderboard.
3. Open http://localhost:8000/docs. This page is generated from the code.
4. Open http://localhost:8000/health.

Note: free-tier models on OpenRouter are shared and sometimes answer "overloaded" or
"rate-limited". The app retries each model call up to `LLM_MAX_ATTEMPTS` times, then reports
the error in the chat. Resend if that happens. Reasoning models also spend seconds "thinking"
before the first word; `LLM_REASONING=low` in `.env` keeps that short. The default model is
`poolside/laguna-s-2.1:free`, which answers in a few seconds; change `LLM_MODEL` to try another.

Try this too: reload the page mid-conversation. The chat log is empty, but the Oracle still
remembers you. The session id lives in the browser's `sessionStorage` and the history lives in
the server process. Ask the room where each of those would have to live in the cloud.

## 3. Concepts for people who have never run a server (10 min)

- **A server is a long-running process** that waits for requests. Here that process is
  `uvicorn`, and `make run` starts it. Your notebook runs and exits; a server runs until
  something stops it.
- **A port is a numbered door** on a machine. Ours is 8000. Two processes cannot share a
  port, which is why "address already in use" is the first error every backend engineer
  learns.
- **HTTP request and response.** A method (`GET`, `POST`), a path (`/predict/marriage`),
  headers, a body (JSON), and a status code back. Try it:

  ```bash
  curl -X POST localhost:8000/predict/marriage \
    -H 'Content-Type: application/json' \
    -d '{"age": 30, "relationship_status": "dating", "coffee_cups_per_day": 3,
         "coding_hours_per_week": 40, "side_projects": 1, "unread_slack_messages": 120}'
  ```

- **Status codes we use:** 200 worked; 422 your input failed validation, and the body
  says which field; 502 the LLM provider failed; 503 the app is up but not configured
  (no API key).
- **Streaming.** A normal response arrives all at once. A streamed response is one
  connection that stays open while the server pushes pieces; `/chat/stream` does this with
  Server-Sent Events, a plain-text format of `event:` and `data:` lines. Users see the first
  word in a second instead of staring at a spinner for ten.
- **Environment variables** are configuration that lives outside the code. Locally they
  come from `.env`; in the cloud they come from a secret manager. `.env` is never committed.
- **Dependency locking.** `pyproject.toml` says what you want. `uv.lock` records exactly
  what you got, down to the hash. `uv sync` reproduces that anywhere, which is the whole
  point.
- **The docs page.** FastAPI reads the Pydantic models and generates `/docs`. That page is
  your API contract, and it cannot drift from the code because it is the code.

## 4. Code walkthrough (30 min)

Read the files in this order. One or two points each.

1. `app/config.py`. One `Settings` object. Every value can be overridden by an env var of
   the same name. Nothing else in the app reads the environment.
2. `app/schemas.py`. Types are the contract. The `Literal` enums come from
   `app/ml/features.py`, so the API only accepts values the model was trained on. Try a
   bad value in `/docs` and read the 422.
3. `app/routers/predict.py`. An endpoint is a function. The model is not global state; it
   hangs off `app.state` and the function asks for it.
4. `app/ml/predict.py` and `app/ml/features.py`. Artifacts load once at startup, not per
   request. Training and serving share `build_feature_frame`, so the feature code cannot
   drift between them.
5. `training/train_income.py`. The model is a file. The metrics are a file. The version
   string travels inside the artifact and comes back out in every prediction response.
   Today's numbers from `artifacts/income_metrics.json`:

   | Metric | Value |
   |---|---|
   | Training rows | 14,292 |
   | Holdout rows | 3,573 |
   | Mean absolute error | about 29,000 USD |
   | Median absolute percentage error | about 25% |

   Good enough for a fortune teller. Ask the room whether it would be good enough for a
   salary tool, and what they would need to answer that.
6. `app/agent/graph.py`. Draw the two-node loop on the whiteboard. The `agent` node asks
   the LLM; if the answer contains tool calls, the `tools` node runs them and we loop; if
   not, we stop. That loop is the entire agent.
7. `app/agent/tools.py`. The agent is a client of our own API. It calls
   `MODEL_API_URL`, which today is this same process. On Day 5 that becomes another
   container, and only the env var changes.
8. `app/routers/chat.py`. The browser's session id is the memory key. We count which tools
   ran in this turn by comparing message counts before and after. There are two endpoints:
   `/chat` returns one JSON reply (easy to curl and test), and `/chat/stream` pushes tokens as
   Server-Sent Events so the page can show words as they arrive. Same graph, same memory;
   only the delivery differs. Watch the network tab while chatting to see the stream.
9. `app/main.py`. The lifespan function wires everything once at startup: settings,
   models, store, agent graph.
10. `static/index.html`. Plain fetch calls. The page knows nothing the API does not
    publish; even the dropdown values come from `/options`.

## 5. Deliberate shortcuts and which day fixes each (5 min)

| Shortcut | Fixed on |
|---|---|
| Model artifacts and the data CSV are committed to git, so nobody has to download the 141 MB raw survey to run the app | Day 6 (registry) and Day 7 (data versioning) |
| Chat memory and leaderboard live in process memory | Day 5 (database) |
| The API key sits in a `.env` file | Day 4 (secrets) |
| Agent and models run in one process | Day 5 (service split) |
| No logs, no metrics, no tracing | Day 8 (observability) |
| Runs only on your laptop | Day 2 (containers), Day 4 (cloud), Day 9 (Kubernetes) |

## 6. Assignment briefing (5 min)

See `ASSIGNMENT.md`.

## Reference

```bash
make install     # uv sync
make run         # start the server with reload
make test        # pytest, no key or network needed
make lint        # ruff check + format check
make train       # rebuild the slim CSV and both model artifacts. The first run downloads the
                 # 141 MB raw survey file. You do not need this to run the app.
make probe       # check that your OpenRouter model can call tools
make docker-build   # build the image oracle:day1 (Docker Desktop must be running)
make docker-run     # run it on port 8000 with the key from .env
```

The handout `docker-explained.html` in this folder walks through the Dockerfile line by line.
