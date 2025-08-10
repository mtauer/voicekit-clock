import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.voicekit_clock_stack import (
    VoicekitClockStack,
)


# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_stack/cdk_stack_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = VoicekitClockStack(app, "voicekit-clock-stack")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
