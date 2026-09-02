# Deploying the Oracle to EC2, by hand

The deliberately manual path: a rented Linux machine, the image copied up as a file, a
container started over SSH. Every step here is something a later day automates. Budget
about 20 minutes the first time.

## The setup we all use

| Choice | Value |
|---|---|
| Region | Europe (London), `eu-west-2` |
| AMI | Amazon Linux 2023, **64-bit (x86)** |
| Instance type | **t2.small** |
| Storage | 16 GB gp3 |
| Image | `oracle:day1-amd64`, built with the command in Step 1 |

The course account only permits the `t2` instance family, and only in London. Anything
else fails at launch with "explicit deny in a service control policy". The `t2` machines
are x86, so everyone builds an x86 (amd64) image, whatever laptop they have.

## Before you start

- Docker Desktop (Mac, Windows) or Docker Engine (Linux) installed and running.
- Access to the AWS console for the course account, region set to **Europe (London)**.
- Your `day01/oracle/.env` with your OpenRouter key in it.
- A terminal: Terminal on Mac, any shell on Linux, **PowerShell** on Windows (it has
  `ssh` and `scp` built in on Windows 10 and later).

## Step 1. Build an x86 image and export it to a file

One build command for every operating system. On an Apple Silicon Mac it builds under
emulation and takes a few minutes longer.

```bash
cd day01/oracle
docker build --platform linux/amd64 -t oracle:day1-amd64 .
```

Export it. An image is a file.

Mac or Linux:

```bash
docker save oracle:day1-amd64 | gzip > oracle-day1.tar.gz
ls -lh oracle-day1.tar.gz        # roughly 250 to 300 MB
```

Windows (PowerShell):

```powershell
docker save -o oracle-day1.tar oracle:day1-amd64
```

The Windows file is uncompressed and larger, which is fine; `docker load` accepts both.
Do not commit this file.

## Step 2. Launch the instance (AWS console)

1. Open **EC2**, click **Launch instance**.
2. **Name:** `oracle-<yourname>`.
3. **Application and OS Images:** Amazon Linux 2023, Architecture **64-bit (x86)**.
4. **Instance type:** `t2.small`.
5. **Key pair:** Create new key pair. Name it `oracle-<yourname>`, type RSA, format
   `.pem`. The browser downloads it once. Do not lose it; there is no second download.
6. **Network settings**, click **Edit**:
   - Allow SSH traffic from **My IP**.
   - **Add security group rule**: Type Custom TCP, Port range `8000`, Source `0.0.0.0/0`.
     This is the door the browser will use.
7. **Configure storage:** 16 GiB.
8. **Launch instance**. Wait for the state to say **Running**, then copy the
   **Public IPv4 address**. Everywhere below, replace `INSTANCE_IP` with it.

Note: "My IP" is your current public address. If you change networks, SSH stops working
until you edit that rule.

## Step 3. Connect and install Docker

First fix the key file's permissions, then connect. On Mac and Linux:

```bash
chmod 400 ~/Downloads/oracle-<yourname>.pem
ssh -i ~/Downloads/oracle-<yourname>.pem ec2-user@INSTANCE_IP
```

On Windows (PowerShell), `chmod` does not exist; restrict the file to your user instead:

```powershell
icacls $env:USERPROFILE\Downloads\oracle-<yourname>.pem /inheritance:r /grant:r "$env:USERNAME:R"
ssh -i $env:USERPROFILE\Downloads\oracle-<yourname>.pem ec2-user@INSTANCE_IP
```

Type `yes` at the fingerprint question. You are now on the server. Install Docker:

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

The `exit` matters: group membership only applies to new logins.

## Step 4. Copy the image and the secret up

From your laptop, in `day01/oracle`. Mac or Linux:

```bash
scp -i ~/Downloads/oracle-<yourname>.pem oracle-day1.tar.gz .env ec2-user@INSTANCE_IP:~
```

Windows (PowerShell):

```powershell
scp -i $env:USERPROFILE\Downloads\oracle-<yourname>.pem oracle-day1.tar .env ec2-user@INSTANCE_IP:~
```

The upload is the slow part. Note what you just did with `.env`: your key now lives on a
server's disk. Day 4 fixes that.

## Step 5. Load and run (on the server)

```bash
ssh -i <your key> ec2-user@INSTANCE_IP
docker load -i oracle-day1.tar.gz        # or oracle-day1.tar on Windows uploads
docker run -d --restart unless-stopped -p 8000:8000 --env-file .env --name oracle oracle:day1-amd64
docker ps
docker logs -f oracle                    # Ctrl+C stops watching; the container keeps running
```

- `-d` runs it in the background so closing SSH does not kill it.
- `--restart unless-stopped` brings it back after a reboot.
- `--env-file .env` hands the key in at run time, exactly as on your laptop.

Open **http://INSTANCE_IP:8000** in a browser. It is plain http, so the browser will say
"Not secure". That is correct for now and is a Day 4 topic. Chat with the Oracle; the
model calls go from the server to OpenRouter, not through your laptop.

## Step 6. The update loop (this is the lesson)

Change one line locally, for example the welcome message in `static/index.html`. Then
repeat: build, export, upload, load, replace the container.

```bash
# laptop
docker build --platform linux/amd64 -t oracle:day1-amd64 .
docker save oracle:day1-amd64 | gzip > oracle-day1.tar.gz      # Windows: docker save -o oracle-day1.tar oracle:day1-amd64
scp -i <your key> oracle-day1.tar.gz ec2-user@INSTANCE_IP:~

# server
docker load -i oracle-day1.tar.gz
docker rm -f oracle
docker run -d --restart unless-stopped -p 8000:8000 --env-file .env --name oracle oracle:day1-amd64
```

Six commands and a 300 MB upload for a one-line change. Ask yourself how you feel about
doing this ten times a day.

## Step 7. Clean up

- **Stop** the instance from the console when you are done for the day. Stopped instances
  cost almost nothing, but the public IP changes when you start it again.
- **Terminate** it when you are done with it for good.
- Delete the exported image file from your laptop.

## Things that go wrong, and what they teach

| Symptom | Cause | Lesson |
|---|---|---|
| `explicit deny in a service control policy` on launch | Instance type outside `t2`, or a region other than London | Organisation policies outrank account admins |
| Browser hangs on `INSTANCE_IP:8000` | No security group rule for port 8000 | Networks are closed by default |
| `Permissions ... are too open` on ssh | Key file permissions not restricted | Private keys are private |
| `ssh: connect ... timed out` | SSH rule was set to a previous network's IP | Firewalls key on source address |
| `exec format error` when starting the container | You exported an arm64 image (built without `--platform`) | Images are built for a CPU architecture |
| `permission denied ... docker.sock` | Did not log out after `usermod` | Unix groups apply at login |
| App vanished after closing the terminal | Forgot `-d` | Foreground processes die with their shell |
| Chat says "The Oracle is asleep" | Forgot `--env-file .env` | Secrets are supplied at run time |
| Works, then gone after a reboot | No `--restart` policy | Servers restart; plan for it |

## The registry alternative

Instead of exporting and uploading a file, push the image to a registry and pull it on the
server. Skips the big upload and is how teams do it, at the cost of an account and a login
step on the box:

```bash
# laptop
docker tag oracle:day1-amd64 ghcr.io/YOUR_GITHUB_USER/oracle:day1
docker push ghcr.io/YOUR_GITHUB_USER/oracle:day1        # make the package public in GitHub

# server
docker pull ghcr.io/YOUR_GITHUB_USER/oracle:day1
```

We come back to this when we introduce ECR.
