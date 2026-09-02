# Day 1 assignment: run it, extend it, break it

Due before Day 2. Submit a link to your fork or a zip, plus the written answers.

## 1. Run the Oracle (warm-up)

1. Create a free account at openrouter.ai and generate an API key.
2. `cd day01/oracle && cp .env.example .env`, paste your key into `.env`.
3. `make install && make run`, open http://localhost:8000.
4. Have a full conversation until all three tools have been used. Take a screenshot.
5. Run `make test` and paste the last line of the output.

## 2. Add a new prophecy (the real work)

Add one new prediction endpoint and matching agent tool. Ideas:

- `POST /predict/burnout`: years until burnout from meetings per week, on-call weeks per
  year, and unread emails.
- `POST /predict/friday-deploy`: probability the deploy breaks, from lines changed, tests
  passing, and hour of day.
- Your own idea, as long as it takes at least three inputs and returns a number.

Requirements:

- A Pydantic request and response model in `app/schemas.py` with sensible ranges.
- The endpoint in `app/routers/predict.py`. A formula is fine; a trained model is a bonus.
- A tool in `app/agent/tools.py` that calls your endpoint over HTTP, registered in
  `ORACLE_TOOLS`.
- Update `app/agent/persona.py` so the Oracle knows to collect the inputs and use the tool.
- One test in `tests/` for the endpoint: valid input returns 200 with your fields; invalid
  input returns 422.
- `make test` and `make lint` both pass.

## 3. Written answers (short, three or four sentences each)

1. Two people open the page and, by accident, end up with the same session id. What does
   each of them see and why?
2. Restart the server. What happened to the leaderboard and the chat history, and which
   part of the code explains it?
3. Set `MODEL_API_URL=http://localhost:9999` in `.env` and try to get a fortune. What does
   the Oracle say, and which line of code turned the failure into that message?
