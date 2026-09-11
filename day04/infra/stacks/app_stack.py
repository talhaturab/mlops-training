"""OracleAppStack: deployed by the pipeline on every merge to main.

    npx aws-cdk deploy OracleAppStack -c image_tag=<commit sha>

Everything that runs the app: a small network, a Postgres database, and an ECS Express
service, which is Fargate plus a load balancer plus an HTTPS URL, managed by ECS.
The only input that changes between deploys is `image_tag`, so a deploy is
CloudFormation noticing "the tag changed" and telling ECS to roll out that image.
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

# The OpenRouter key is created by hand, once, so it is never in git or in the pipeline:
#   aws secretsmanager create-secret --name oracle/openrouter --secret-string sk-or-...
OPENROUTER_SECRET_NAME = "oracle/openrouter"


class OracleAppStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # --- 1. Network ---------------------------------------------------------------------
        # A VPC is a private network inside AWS. Both the database and the containers live
        # in it. Two subnet types: "public" ones have a route to the internet, "isolated"
        # ones have none at all. Containers go in public (they must pull the image from ECR
        # and call OpenRouter); the database goes in isolated, so nothing outside can reach it.
        # nat_gateways=0 because nothing in the isolated subnets needs to call out, and a
        # NAT gateway costs about $35 a month.
        vpc = ec2.Vpc(
            self,
            "Vpc",
            availability_zones=["eu-west-2a", "eu-west-2b,"],
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="db", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            ],
        )
        

        # --- 2. Database --------------------------------------------------------------------
        # A managed Postgres on the smallest instance. RDS generates the password itself and
        # stores it in Secrets Manager; we never see it and never write it down.
        # RemovalPolicy.DESTROY so `cdk destroy` really removes it (default: keep a snapshot).
        db = rds.DatabaseInstance(
            self,
            "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            database_name="oracle",
            credentials=rds.Credentials.from_generated_secret("oracle"),
            allocated_storage=20,
            storage_encrypted=True,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
        )

        # --- 3. The firewall rule between the containers and the database --------------------
        # A security group is a firewall attached to a resource. The containers get this one;
        # the database is told to accept port 5432 from it, and from nothing else.
        task_sg = ec2.SecurityGroup(self, "TaskSecurityGroup", vpc=vpc)
        db.connections.allow_default_port_from(task_sg)

        # --- 4. Two roles ECS needs -----------------------------------------------------------
        # The execution role is what ECS uses to START a container: pull the image from ECR,
        # fetch the secrets, write logs. It is not what the app runs as.
        openrouter = secretsmanager.Secret.from_secret_name_v2(
            self, "OpenRouterSecret", OPENROUTER_SECRET_NAME
        )
        execution_role = iam.Role(
            self,
            "ExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )
        db.secret.grant_read(execution_role)
        openrouter.grant_read(execution_role)

        # The infrastructure role is what ECS Express uses to BUILD the parts around the
        # containers: the load balancer, its security groups, the certificate, auto scaling.
        infrastructure_role = iam.Role(
            self,
            "InfrastructureRole",
            assumed_by=iam.ServicePrincipal("ecs.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
                )
            ],
        )

        # --- 5. The service -----------------------------------------------------------------
        # The repository was created by OracleBaseStack. Referring to it by name keeps the
        # two stacks independent: this one only needs the repository to exist.
        repository = ecr.Repository.from_repository_name(self, "Repository", "oracle")

        # Which image to run. The pipeline passes the commit sha: -c image_tag=39081f6
        image_tag = self.node.get_context("image_tag")

        # One resource. ECS creates the cluster, task definition, load balancer, HTTPS
        # certificate, log group, auto scaling and rollback alarm from it.
        # Cpu and memory are in task units: 512 = half a vCPU, 1024 = 1 GB. Enough for a
        # class, and about half the price of the 1 vCPU / 2 GB we chose in the console.
        service = ecs.CfnExpressGatewayService(
            self,
            "Service",
            service_name="oracle",
            infrastructure_role_arn=infrastructure_role.role_arn,
            execution_role_arn=execution_role.role_arn,
            cpu="512",
            memory="1024",
            # Ask /health, not just "is the port open". A rollout whose /health fails, or
            # that starts returning 5xx, is rolled back to the previous image.
            health_check_path="/health",
            primary_container=ecs.CfnExpressGatewayService.ExpressGatewayContainerProperty(
                image=f"{repository.repository_uri}:{image_tag}",
                container_port=8000,
                # Plain settings: visible in the console, fine to be visible.
                environment=[
                    ecs.CfnExpressGatewayService.KeyValuePairProperty(name=k, value=v)
                    for k, v in {
                        "DB_HOST": db.db_instance_endpoint_address,
                        "DB_PORT": db.db_instance_endpoint_port,
                        "DB_NAME": "oracle",
                        "DB_USER": "oracle",
                    }.items()
                ],
                # Secrets: ECS fetches these when the container starts and puts them in
                # its environment. They never appear in the template or the console.
                # "<secret arn>:password::" means "the password field of that JSON secret".
                secrets=[
                    ecs.CfnExpressGatewayService.SecretProperty(
                        name="DB_PASSWORD", value_from=f"{db.secret.secret_arn}:password::"
                    ),
                    ecs.CfnExpressGatewayService.SecretProperty(
                        name="OPENROUTER_API_KEY", value_from=openrouter.secret_arn
                    ),
                ],
            ),
            # Public subnets, so ECS makes an internet-facing load balancer and gives each
            # container a public IP for outgoing calls. Our security group is added on top
            # of the ones ECS creates, which is what lets the database recognise the tasks.
            network_configuration=ecs.CfnExpressGatewayService.ExpressGatewayServiceNetworkConfigurationProperty(
                subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids,
                security_groups=[task_sg.security_group_id],
            ),
            # How many copies. One is enough for a class; ECS adds more when CPU is busy.
            scaling_target=ecs.CfnExpressGatewayService.ExpressGatewayScalingTargetProperty(
                min_task_count=1, max_task_count=2
            ),
        )
        # The roles must exist before ECS tries to use them.
        service.node.add_dependency(execution_role, infrastructure_role)

        # ECS gives the service its own HTTPS address: https://oracle.ecs.eu-west-2.on.aws
        CfnOutput(self, "ServiceUrl", value=service.attr_endpoint)
        CfnOutput(self, "ImageTag", value=image_tag)
