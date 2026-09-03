# Day 2 assignment: your own pipeline

Due before Day 3.

## 1. Make it yours

1. Fork the course repo on GitHub (your own copy under your account).
2. In your fork, Settings → Secrets and variables → Actions:
   - variable `EC2_HOST` = your instance's public IP from Day 1
   - variable `EC2_USER` = `ec2-user`
   - secret `EC2_SSH_KEY` = the full contents of your `.pem` file, including the
     `BEGIN` and `END` lines
3. In the EC2 console, edit your instance's security group: change the SSH rule's
   source from your IP to `0.0.0.0/0`. GitHub's runners need to reach port 22.
4. Push any small change to `day01/oracle` on `main`. Watch the Actions tab.
5. The first run creates the package `ghcr.io/<your-username>/oracle`. The deploy job logs
   the server in with the run's own token, so it works even while the package is private.
   Make it public anyway (Packages → oracle → Package settings → Change visibility) so
   `docker pull` works from anywhere without a login.
6. Screenshot the green run and the page on your instance showing your change.

## 2. Break it on purpose

1. Edit one test in `day01/oracle/tests` so it fails. Push.
2. Screenshot the red run. Note which jobs never started.
3. Revert the change and push again.

## 3. Ship your Day 1 extension

Merge the endpoint and tool you built for the Day 1 assignment into your fork's `main`
through a pull request. Watch the tests run on the pull request before you merge. After
the merge, confirm your new tool works on the deployed instance.

## 4. Written answers (three or four sentences each)

1. Two people push to `main` thirty seconds apart. Describe what happens on the server,
   using the `concurrency` block in the workflow.
2. The deploy job pulls `oracle:<sha>` rather than `oracle:latest`. What could go wrong
   if it pulled `latest`?
3. The OpenRouter key never appears in the workflow. Where is it, and what would you have
   to do to rotate it today?
