from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
)
from constructs import Construct

import os


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

        # Lambda function that synthesizes/serves MP3
        audio_get_fn = _lambda.Function(
            self,
            "AudioGetHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="audio_get.handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "..", "lambda")
            ),
            timeout=Duration.seconds(15),
            memory_size=512,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                # Defaults tuned for German (focused on natural synthesis)
                "DEFAULT_VOICE_ID": "Daniel",  # 'Vicky' or 'Daniel' for generative engine
                "DEFAULT_ENGINE": "generative",  # 'standard', 'neural', 'long-form', or 'generative'
                "DEFAULT_OUTPUT_FORMAT": "mp3",
                "DEFAULT_SAMPLE_RATE": "24000",  # '8000', '16000', '22050', or '24000'
            },
        )

        # Allow Lambda to read/write S3 and synthesize with Polly
        bucket.grant_read_write(audio_get_fn)
        audio_get_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["polly:SynthesizeSpeech"],
                resources=["*"],  # Polly SynthesizeSpeech generally requires '*'
            )
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
            api_key_required=True,  # lock it down with API key
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
