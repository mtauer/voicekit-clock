#!/usr/bin/env python3

import aws_cdk as cdk

from stacks.voicekit_clock_stack import (
    VoicekitClockStack,
)


app = cdk.App()
VoicekitClockStack(
    app,
    "VoicekitClockStack",
)

app.synth()
