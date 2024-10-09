from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_apigateway as apigateway,
    aws_iam as iam,
    core
)

import aws_cdk.aws_lambda_event_sources as lambda_event_sources
from aws_cdk.aws_s3_notifications import LambdaDestination
from constructs import Construct



class ImageServiceStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 bucket to store images and thumbnails
        image_bucket = s3.Bucket(self, "ImageBucket", versioned=True)

        # SQS Queue for thumbnail generation requests
        thumbnail_queue = sqs.Queue(self, "ThumbnailQueue")

        # Lambda role with S3 and SQS access
        lambda_role = iam.Role(self, "LambdaExecutionRole",
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                               managed_policies=[
                                   iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                                   iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                                   iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess")
                               ])

        # Lambda function for image upload
        upload_lambda = _lambda.Function(
            self, "UploadImageLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="upload_image.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': image_bucket.bucket_name,
                'QUEUE_URL': thumbnail_queue.queue_url
            },
            role=lambda_role
        )

        # Lambda function to generate thumbnails
        thumbnail_lambda = _lambda.Function(
            self, "GenerateThumbnailLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="generate_thumbnail.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': image_bucket.bucket_name
            },
            role=lambda_role
        )

        # Lambda triggered by SQS to generate thumbnails
        thumbnail_lambda.add_event_source(lambda_event_sources.SqsEventSource(thumbnail_queue))

        # Lambda for downloading images and thumbnails
        download_lambda = _lambda.Function(
            self, "DownloadImageLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="download_image.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': image_bucket.bucket_name
            },
            role=lambda_role
        )

        # API Gateway for upload, download and thumbnail retrieval
        api = apigateway.RestApi(self, "ImageServiceApi")

        # API endpoints
        upload_resource = api.root.add_resource("upload")
        upload_resource.add_method("POST", apigateway.LambdaIntegration(upload_lambda))

        download_resource = api.root.add_resource("download")
        download_resource.add_method("GET", apigateway.LambdaIntegration(download_lambda))

        thumbnail_resource = api.root.add_resource("thumbnail")
        thumbnail_resource.add_method("GET", apigateway.LambdaIntegration(download_lambda))

        # Add S3 event notification to the upload lambda
        #image_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3_notifications.LambdaDestination(upload_lambda))
