from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
)
from aws_cdk import aws_lambda_python_alpha as lambda_python
from constructs import Construct
from dotenv import load_dotenv
import os

load_dotenv()


WEATHER_API_BASE_URL = os.environ["WEATHER_API_BASE_URL"]
WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
WEATHER_API_LOCATION = os.environ["WEATHER_API_LOCATION"]
CONTENTFUL_SPACE_ID = os.environ["CONTENTFUL_SPACE_ID"]
CONTENTFUL_ACCESS_TOKEN = os.environ["CONTENTFUL_ACCESS_TOKEN"]
INCLUDE_BIRTHDAY_CALENDAR = os.environ["INCLUDE_BIRTHDAY_CALENDAR"]

# Bedrock retires models on a schedule, and requests to a retired model fail
# (Claude Sonnet 4, used here before, stopped answering on 2026-10-14). The
# model card gives Claude Sonnet 4.6 an "EOL no sooner than" date of
# 2027-02-17, with at least 6 months' notice before the end. Check the
# model's state before relying on it:
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html
#
# Claude Haiku 5.5 (end of life no sooner than 2027-10-07) is the preferred
# successor, but on 2026-10-20 AWS had not yet released it to this account:
# calls failed with "not available for this account" although its agreement
# was AVAILABLE. Switch once a test call in the target account succeeds.
BEDROCK_REGION = "eu-central-1"
BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-6"
# The EU cross-region profile keeps requests (including the birthday data)
# within EU regions.
BEDROCK_INFERENCE_PROFILE_ID = f"eu.{BEDROCK_MODEL_ID}"
# Regions the EU profile may route to when called from BEDROCK_REGION, taken
# from the "Geo: EU" table on the model card. Re-check it when the model
# changes, as the IAM policy below must name every one of them.
BEDROCK_EU_DESTINATION_REGIONS = [
    "eu-central-1",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "eu-west-1",
    "eu-west-3",
]


class VoicekitClockStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for cached audio
        bucket = s3.Bucket(
            self,
            "CachedAudioBucket",
            bucket_name=None,  # let CDK name it uniquely
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # GET /audio
        audio_get_fn = _lambda.Function(
            self,
            "AudioGetHandler",
            handler="api.audio.get.index.handler",  # <file path>.<function name>
            code=_lambda.Code.from_asset("lambda"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,  # or X86_64; ARM is cheaper
            memory_size=256,
            timeout=Duration.seconds(15),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                # text-to-speech options tuned for German (focused on natural synthesis)
                "TTS_VOICE_ID": "Daniel",  # 'Vicky' or 'Daniel' for generative engine
                "TTS_ENGINE": "generative",  # 'standard', 'neural', 'long-form', or 'generative'
                "TTS_OUTPUT_FORMAT": "mp3",
                "TTS_SAMPLE_RATE": "24000",  # '8000', '16000', '22050', or '24000'
            },
        )

        # Allow lambda to read/write S3 and synthesize with Polly
        bucket.grant_read_write(audio_get_fn)
        audio_get_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["polly:SynthesizeSpeech"],
                resources=["*"],  # Polly SynthesizeSpeech generally requires '*'
            )
        )

        # POST /next-actions
        next_actions_post_fn = lambda_python.PythonFunction(
            self,
            "NextActionsPostHandler",
            entry="lambda",
            index="api/next_actions/post/index.py",  # file name
            handler="handler",  # function name
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,  # or X86_64; ARM is cheaper
            memory_size=256,
            timeout=Duration.seconds(60),
            environment={
                "BEDROCK_REGION": BEDROCK_REGION,
                "BEDROCK_MODEL_ID": BEDROCK_INFERENCE_PROFILE_ID,
                "WEATHER_API_BASE_URL": WEATHER_API_BASE_URL,
                "WEATHER_API_KEY": WEATHER_API_KEY,
                "WEATHER_API_LOCATION": WEATHER_API_LOCATION,
                "WEATHER_API_LANG": "de",
                "CONTENTFUL_SPACE_ID": CONTENTFUL_SPACE_ID,
                "CONTENTFUL_ACCESS_TOKEN": CONTENTFUL_ACCESS_TOKEN,
                "INCLUDE_BIRTHDAY_CALENDAR": INCLUDE_BIRTHDAY_CALENDAR,
            },
        )

        # Bedrock requires both inference profile and foundation model
        # permissions. The profile defines routing and usage, while the models
        # must be explicitly listed (often across regions).
        #
        # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html

        # Allow invoking the EU inference profile
        LLM_INFERENCE_PROFILE_ARN = f"arn:aws:bedrock:{BEDROCK_REGION}:{self.account}:inference-profile/{BEDROCK_INFERENCE_PROFILE_ID}"
        next_actions_post_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                ],
                resources=[LLM_INFERENCE_PROFILE_ARN],
            )
        )

        # Allow invoking the routed foundation models
        DEST_LLM_MODEL_ARNS = [
            f"arn:aws:bedrock:{region}::foundation-model/{BEDROCK_MODEL_ID}"
            for region in BEDROCK_EU_DESTINATION_REGIONS
        ]
        next_actions_post_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                ],
                resources=DEST_LLM_MODEL_ARNS,
                conditions={
                    "StringLike": {
                        "bedrock:InferenceProfileArn": LLM_INFERENCE_PROFILE_ARN
                    }
                },
            )
        )

        # GET /health
        health_get_fn = _lambda.Function(
            self,
            "HealthGetHandler",
            handler="api.health.get.index.handler",  # <file path>.<function name>
            code=_lambda.Code.from_asset("lambda"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,  # or X86_64; ARM is cheaper
            memory_size=128,
            timeout=Duration.seconds(5),
        )

        # API Gateway with binary media type for MP3 and API key requirement
        api = apigw.RestApi(
            self,
            "VoicekitClockApi",
            rest_api_name="voicekit-clock-api",
            description="Logic and MP3 synthesis for the Voice Kit Clock",
            binary_media_types=["audio/mpeg"],  # allow binary pass-through for MP3
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=50,
                throttling_burst_limit=100,
            ),
        )

        audio_res = api.root.add_resource("audio")
        audio_res.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(audio_get_fn),
            api_key_required=True,
        )

        next_actions_res = api.root.add_resource("next-actions")
        next_actions_res.add_method(
            http_method="POST",
            integration=apigw.LambdaIntegration(next_actions_post_fn),
            api_key_required=True,
        )

        health_res = api.root.add_resource("health")
        health_res.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(health_get_fn),
            api_key_required=True,
        )

        # Create an API key + usage plan and connect it to the stage/method
        api_key = api.add_api_key("ClientApiKey")
        plan = api.add_usage_plan(
            "UsagePlan",
            name="DefaultUsagePlan",
            throttle=apigw.ThrottleSettings(rate_limit=50, burst_limit=100),
            quota=apigw.QuotaSettings(limit=10000, period=apigw.Period.MONTH),
        )
        plan.add_api_key(api_key)
        plan.add_api_stage(stage=api.deployment_stage)
