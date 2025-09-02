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
                "BEDROCK_REGION": "eu-central-1",
                "BEDROCK_MODEL_ID": "eu.anthropic.claude-sonnet-4-20250514-v1:0",
                "WEATHER_API_BASE_URL": WEATHER_API_BASE_URL,
                "WEATHER_API_KEY": WEATHER_API_KEY,
                "WEATHER_API_LOCATION": WEATHER_API_LOCATION,
                "WEATHER_API_LANG": "de",
            },
        )

        # Bedrock requires both inference profile and foundation model
        # permissions. The profile defines routing and usage, while the models
        # must be explicitly listed (often across regions).
        #
        # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html

        # Allow invoking the EU Sonnet 4 inference profile
        LLM_INFERENCE_PROFILE_ARN = f"arn:aws:bedrock:eu-central-1:{self.account}:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0"
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
            # EU destinations for the EU Claude Sonnet 4 profile
            "arn:aws:bedrock:eu-central-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:eu-north-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:eu-south-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
            "arn:aws:bedrock:eu-south-2::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
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
