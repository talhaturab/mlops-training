"""OracleBaseStack: deployed once, by hand. Nothing in here changes when the app changes.

    npx aws-cdk deploy OracleBaseStack --profile talhasandbox

It creates two things:
  1. the ECR repository the pipeline pushes images into
  2. an IAM role that GitHub Actions is allowed to assume, with no password or access key
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from constructs import Construct

GITHUB_OIDC_URL = "https://token.actions.githubusercontent.com"


class OracleBaseStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # --- 1. The image repository -------------------------------------------------------
        # Day 3 you clicked "Create repository". This is the same thing.
        # RemovalPolicy.DESTROY + empty_on_delete: `cdk destroy` removes it and its images.
        # The default would keep the repository so you never lose images by accident.
        self.repository = ecr.Repository(
            self,
            "Repository",
            repository_name="oracle",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )

        # --- 2. Trust GitHub ----------------------------------------------------------------
        # GitHub Actions can prove "this job is running for repo X on branch Y" by presenting
        # a signed token. An OIDC provider tells AWS to accept tokens signed by GitHub.
        # An account can have only one provider for GitHub, and this account already has one
        # (another project made it), so we refer to it instead of creating it. In an empty
        # account you would create it:
        #   iam.OidcProviderNative(self, "GitHubProvider", url=GITHUB_OIDC_URL,
        #                          client_ids=["sts.amazonaws.com"])
        provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self,
            "GitHubProvider",
            f"arn:aws:iam::{self.account}:oidc-provider/{GITHUB_OIDC_URL[8:]}",
        )

        # Which repository and branch may use the role. Set in cdk.json as "owner/name".
        owner, name = self.node.get_context("github_repo").split("/")

        # The token GitHub signs names the repository in its "sub" claim. Older repositories
        # get "repo:owner/name:ref:refs/heads/main". Repositories created since 2025 get an
        # "immutable subject" with numeric ids, "repo:owner@123/name@456:ref:...", so that
        # renaming the repository cannot break or hijack the trust. We accept both spellings.
        #   check yours: gh api repos/OWNER/NAME/actions/oidc/customization/sub
        subjects = [
            f"repo:{owner}/{name}:ref:refs/heads/main",
            f"repo:{owner}@*/{name}@*:ref:refs/heads/main",
        ]

        # The role the pipeline assumes. The conditions are the whole security model:
        # only jobs from THIS repo on THIS branch get credentials, and they last one hour.
        deploy_role = iam.Role(
            self,
            "GitHubDeployRole",
            role_name="oracle-github-deploy",
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {f"{GITHUB_OIDC_URL[8:]}:aud": "sts.amazonaws.com"},
                    "StringLike": {f"{GITHUB_OIDC_URL[8:]}:sub": subjects},
                },
            ),
            description="Assumed by GitHub Actions to push images and run cdk deploy",
        )

        # What the role may do. Two things only:
        #   a) push to our repository (and log in to ECR, which is an account-wide action)
        self.repository.grant_pull_push(deploy_role)
        deploy_role.add_to_policy(
            iam.PolicyStatement(actions=["ecr:GetAuthorizationToken"], resources=["*"])
        )
        #   b) run `cdk deploy`. CDK does not deploy as this role directly: it switches into the
        #      roles that `cdk bootstrap` created (their names all start with cdk-), and those
        #      roles do the actual work. So the only permission needed is "may switch into them".
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*"],
            )
        )

        # Printed after deploy. The ARN goes into the GitHub repository variable
        # AWS_DEPLOY_ROLE_ARN; the pipeline reads it from there.
        CfnOutput(self, "DeployRoleArn", value=deploy_role.role_arn)
        CfnOutput(self, "RepositoryUri", value=self.repository.repository_uri)
