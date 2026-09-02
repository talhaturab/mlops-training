# Deploying the Oracle to EC2, by hand

This is the deliberately manual path: a rented Linux machine, an image copied up as a
file, and a container started over SSH. Every step you take here is a step a later day
automates. Budget about 20 minutes the first time.

## Recommendation: which image and which machine

**Use the image you already built on your Mac, unchanged, on an Arm instance.**

- Your Mac is Apple Silicon, so `docker build` produced an **arm64** image. That is not a
  "Mac image"; it is a Linux image for Arm CPUs. Linux is the only thing that runs inside
  Docker containers, on any host.
- AWS sells Arm machines (Graviton, the `t4g` family). Pick one and the image runs as is.
  They are also cheaper than the x86 equivalents.
- If you ever must use an x86 instance (`t3`, `t2`, `m5`), rebuild first with
  `docker build --platform linux/amd64 -t oracle:day1 .`, otherwise the container dies
  with `exec format error`. This is a good mistake to show once, not to live with.

So, for this walkthrough:

| Choice | Pick |
|---|---|
| AMI | Amazon Linux 2023, **64-bit (Arm)** |
| Instance type | **t4g.small** (2 vCPU, 2 GB memory) |
| Storage | 16 GB gp3 |
| Image | `oracle:day1` exactly as built on your Mac |

## Before you start

- Docker Desktop running on your Mac, image built: `make docker-build` in `day01/oracle`.
- An AWS account you can log into in the browser.
- Your `day01/oracle/.env` with the OpenRouter key in it.

## Step 1. Export the image to a file (on your Mac)

An image is a file. Write it out and compress it.

```bash
cd "day01/oracle"
docker save oracle:day1 | gzip > oracle-day1.tar.gz
ls -lh oracle-day1.tar.gz        # roughly 250 to 300 MB
```

Do not commit this file. The repo's `.gitignore` already excludes `*.tar.gz`.

## Step 2. Launch the instance (AWS console)

1. Open **EC2**, click **Launch instance**.
2. **Name:** `oracle-day1`.
3. **Application and OS Images:** Amazon Linux 2023. Under **Architecture** choose
   **64-bit (Arm)**. If you leave it on x86 the image from your Mac will not run.
4. **Instance type:** `t4g.small`.
5. **Key pair:** Create new key pair. Name `oracle-day1`, type RSA, format `.pem`.
   The browser downloads it once. Do not lose it; there is no second download.
6. **Network settings**, click **Edit**:
   - Allow SSH traffic from **My IP**.
   - Click **Add security group rule**: Type Custom TCP, Port range `8000`,
     Source `0.0.0.0/0`. This is the door the browser will use.
7. **Configure storage:** 16 GiB.
8. Click **Launch instance**. Wait for the instance state to say **Running**, then
   copy its **Public IPv4 address**. Call it `YOUR_IP` below.

## Step 3. Connect and install Docker (in a terminal on your Mac)

```bash
chmod 400 ~/Downloads/oracle-day1.pem
ssh -i ~/Downloads/oracle-day1.pem ec2-user@YOUR_IP
```

Type `yes` when asked about the host fingerprint. You are now on the server.

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

The `exit` matters: group membership only applies to new logins.

## Step 4. Copy the image and the secret up (on your Mac)

```bash
cd "day01/oracle"
scp -i ~/Downloads/oracle-day1.pem oracle-day1.tar.gz .env ec2-user@YOUR_IP:~
```

The upload is the slow part. Note what you just did with `.env`: the key now lives on a
server's disk. Day 4 fixes that.

## Step 5. Load and run (on the server)

```bash
ssh -i ~/Downloads/oracle-day1.pem ec2-user@YOUR_IP
docker load < oracle-day1.tar.gz
docker run -d --restart unless-stopped -p 8000:8000 --env-file .env --name oracle oracle:day1
docker ps
docker logs -f oracle            # Ctrl+C stops watching; the container keeps running
```

- `-d` runs it in the background so closing SSH does not kill it.
- `--restart unless-stopped` brings it back after a reboot.
- `--env-file .env` hands the key in at run time, exactly as on your laptop.

Open **http://YOUR_IP:8000** in a browser. It is plain http, so the browser will say
"Not secure". That is correct and is a Day 4 topic. Chat with the Oracle; the model calls
go from the server to OpenRouter, not through your laptop.

## Step 6. The update loop (this is the lesson)

Change one line locally, for example the welcome message in `static/index.html`. Then:

```bash
# Mac
make docker-build
docker save oracle:day1 | gzip > oracle-day1.tar.gz
scp -i ~/Downloads/oracle-day1.pem oracle-day1.tar.gz ec2-user@YOUR_IP:~

# server
docker load < oracle-day1.tar.gz
docker rm -f oracle
docker run -d --restart unless-stopped -p 8000:8000 --env-file .env --name oracle oracle:day1
```

Six commands and a 300 MB upload for a one-line change. Ask the room how they feel about
doing this ten times a day.

## Step 7. Clean up

- **Stop** the instance from the console when class ends. Stopped instances cost almost
  nothing, but the public IP changes when you start it again.
- **Terminate** it when you are done with it for good.
- Delete `oracle-day1.tar.gz` from your Mac.

## Things that go wrong, and what they teach

| Symptom | Cause | Lesson |
|---|---|---|
| Browser hangs on `YOUR_IP:8000` | No security group rule for port 8000 | Networks are closed by default |
| `Permissions 0644 ... are too open` on ssh | Key file not `chmod 400` | Private keys are private |
| `exec format error` when starting the container | x86 instance, arm64 image | Images are built for a CPU architecture |
| `permission denied ... docker.sock` | Did not log out after `usermod` | Unix groups apply at login |
| App vanished after closing the terminal | Forgot `-d` | Foreground processes die with their shell |
| Chat says "The Oracle is asleep" | Forgot `--env-file .env` | Secrets are supplied at run time |
| Works, then gone after a reboot | No `--restart` policy | Servers restart; you must plan for it |

## The registry alternative

Instead of `docker save` and `scp`, push the image to a registry and pull it on the
server. Skips the big upload and is how real teams do it, at the cost of an account and a
login step on the box:

```bash
# Mac
docker tag oracle:day1 ghcr.io/YOUR_GITHUB_USER/oracle:day1
docker push ghcr.io/YOUR_GITHUB_USER/oracle:day1        # make the package public in GitHub

# server
docker pull ghcr.io/YOUR_GITHUB_USER/oracle:day1
```

Save this for when you introduce ECR and IAM.
