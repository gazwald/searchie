#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from searchie.searchie_stack import SearchieStack


app = cdk.App()
SearchieStack(
    app,
    "SearchieStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region="ap-southeast-2"
    ),
)

app.synth()
