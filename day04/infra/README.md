# Oracle infrastructure (Day 4)

Two CDK stacks. `OracleBaseStack` is deployed once by hand. `OracleAppStack` is deployed by
GitHub Actions on every merge to `main` (see `.github/workflows/oracle-aws.yml`).

## One-time setup

Run these from this folder, with an active SSO session (`aws sso login --profile talhasandbox`).

```bash
uv sync
npx aws-cdk bootstrap aws://824992912214/eu-west-2 --profile talhasandbox
npx aws-cdk deploy OracleBaseStack --profile talhasandbox
```

The deploy prints `DeployRoleArn`. Give it to GitHub:

```bash
gh variable set AWS_DEPLOY_ROLE_ARN --body "arn:aws:iam::824992912214:role/oracle-github-deploy"
```

Put the OpenRouter key in Secrets Manager, once. It is never in git or in the pipeline:

```bash
aws secretsmanager create-secret --name oracle/openrouter --secret-string "sk-or-..." \
  --region eu-west-2 --profile talhasandbox
```

Then merge to `main`, or run the `oracle-aws` workflow by hand. The first run creates the
network, the database and the service, and takes about 20 minutes; later runs take about 8.

## Day to day

```bash
npx aws-cdk synth                      # write the templates to cdk.out, touch nothing
npx aws-cdk diff OracleAppStack --profile talhasandbox      # what would change
npx aws-cdk deploy OracleAppStack -c image_tag=39081f6 --profile talhasandbox
npx aws-cdk destroy OracleAppStack --profile talhasandbox   # remove everything the pipeline made
```

Uses `npx aws-cdk` so nothing needs installing globally. `npm install -g aws-cdk` gives you a plain `cdk` command instead.
