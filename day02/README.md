# Day 2: The machine does the build

**Goal for the hour:** turn yesterday's six manual commands into one `git push`. By the
end, a push to `main` runs the tests, builds the x86 image, publishes it to a registry, and
replaces the container on your EC2 instance. Same app, same server, no typing.

Files for today:

- `.github/workflows/oracle.yml` at the repo root, the pipeline we read line by line.
- `day02/ci-explained.html`, the concepts handout.
- `day02/oracle-yml-explained.html`, the workflow file explained block by block.
- `day02/ASSIGNMENT.md`, the take-home.

## 0. Before class (instructor)

- The course repo is on GitHub and public. Students fork it.
- Your EC2 instance from Day 1 is running, with `~/.env` on it.
- In the repo settings you have set: variable `EC2_HOST` (the instance IP), variable
  `EC2_USER` (`ec2-user`), and secret `EC2_SSH_KEY` (the contents of the `.pem` file).
- After the first run, flip the package `ghcr.io/<owner>/oracle` to **public** in the
  package settings so students can pull it without a login. The deploy job itself does
  not need this: it logs the server in with the run's token.
- One green run of the workflow before class. Do not demo a pipeline you have not run.

## 1. Name the six steps (10 min)

Put yesterday's update loop on the board and label each line:

| Yesterday you typed | What it really is |
|---|---|
| `make test` (if you remembered) | **test** |
| `docker build --platform linux/amd64 ...` | **build** |
| `docker save`, `scp` | **publish** (badly: a file on one machine) |
| `ssh`, `docker load`, `docker rm -f`, `docker run` | **deploy** |

Every pipeline in the world is those four words. The tools change; the words do not.

## 2. A registry instead of an upload (10 min)

Push the image once by hand so the registry is not magic:

Logging in by hand needs a personal access token, because GitHub passwords do not work
for registries: GitHub → Settings → Developer settings → Personal access tokens →
Tokens (classic) → Generate, scope `write:packages`. Paste it when `docker login` asks
for a password. The pipeline never needs this; it uses the run's own token.

```bash
docker login ghcr.io -u <github-username>
docker tag oracle:day1-amd64 ghcr.io/<owner>/oracle:manual
docker push ghcr.io/<owner>/oracle:manual
```

On the server: `docker pull ghcr.io/<owner>/oracle:manual`. No 300 MB upload from a
laptop; the server fetches it from a neutral place. Point out that `push` sent only the
layers the registry did not already have.

## 3. Read the workflow (15 min)

Open `.github/workflows/oracle.yml`. Read it in this order:

1. `on:` What starts it. Push to `main` and pull requests, only when the app changed.
2. `jobs.test` A fresh Linux machine, checkout, `uv sync --frozen`, ruff, pytest.
   Same commands as your laptop, on a machine nobody has touched. That is the point.
3. `needs:` and `if:` The build waits for tests and only runs on `main`. A red test
   means no image and no deploy. Nothing to remember.
4. `jobs.build-and-push` Buildx, `linux/amd64`, two tags: the commit SHA for machines,
   `latest` for humans. Cache stored in GitHub so a code-only change rebuilds one layer.
5. `permissions: packages: write` and `secrets.GITHUB_TOKEN`. Every run gets a short-lived
   token. Nobody typed a password.
6. `jobs.deploy` The SSH key comes from a secret, the host from a variable, and the
   remote script is the exact four commands from yesterday. Then a health check from
   outside.
7. `concurrency:` Two pushes at once queue, they do not race.

## 4. Live: push, watch, refresh (15 min)

1. Change the welcome line in `day01/oracle/static/index.html`. Commit, push to `main`.
2. Open the Actions tab. Walk through the three jobs as they go green.
3. Refresh `http://<EC2_HOST>:8000`. New text.
4. Now break it: change a test so it fails, push. Red test job, build and deploy never
   start. Revert.

Time it. Six minutes from push to live, and you did nothing.

## 5. What moved where (10 min)

| Thing | Yesterday | Today |
|---|---|---|
| The build | your laptop | a GitHub runner |
| The image | a `.tar.gz` you carried | `ghcr.io/<owner>/oracle:<sha>` |
| The SSH key | `~/Downloads` | a GitHub secret, write-only |
| The server address | your memory | a GitHub variable |
| The OpenRouter key | `.env` on the server | still `.env` on the server (Day 4) |
| Who ran the commands | you | a script anyone can read |

This is the first appearance of "secrets belong to the platform". Day 4 finishes it.

## Reference

```bash
gh run list --workflow oracle          # if you have the GitHub CLI
gh run watch                           # follow the current run
docker pull ghcr.io/<owner>/oracle:latest
```
