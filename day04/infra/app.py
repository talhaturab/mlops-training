"""Entry point. `cdk` runs this file (see cdk.json), and the stacks it creates become templates.

Two stacks, deployed at different times by different people:

  OracleBaseStack  once, by hand, from a laptop.  Things that must exist BEFORE the
                   pipeline can run: the image repository and the IAM role GitHub uses.
  OracleAppStack   on every merge to main, by GitHub Actions.  Everything that runs the app:
                   network, database, ECS Express service.
"""

import os

from aws_cdk import App, Environment

from stacks.app_stack import OracleAppStack
from stacks.base_stack import OracleBaseStack

app = App()

# Account comes from whoever is running cdk (your SSO profile, or the pipeline's role).
# Region is fixed: everything in this course lives in London.
env = Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region="eu-west-2")

OracleBaseStack(app, "OracleBaseStack", env=env)
OracleAppStack(app, "OracleAppStack", env=env)

app.synth()
