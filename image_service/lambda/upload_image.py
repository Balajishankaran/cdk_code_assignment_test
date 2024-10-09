import boto3
import os
import json
import uuid

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

def handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    queue_url = os.environ['QUEUE_URL']

    # Get the image data from the API request
    file_content = event['body'].encode('utf-8')
    file_name = f"{uuid.uuid4()}.jpg"

    # Upload image to S3 bucket
    s3_client.put_object(Body=file_content, Bucket=bucket_name, Key=f"images/{file_name}")

    # Send a message to SQS for thumbnail generation
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({'image_key': f"images/{file_name}"})
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Image uploaded successfully!'})
    }
