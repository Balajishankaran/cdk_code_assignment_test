import boto3
import os

s3_client = boto3.client('s3')

def handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']

    # Get image or thumbnail key from query parameters
    image_key = event['queryStringParameters']['key']

    # Download the image/thumbnail from S3
    image_obj = s3_client.get_object(Bucket=bucket_name, Key=image_key)
    image_data = image_obj['Body'].read()

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'image/jpeg'},
        'body': image_data.encode('base64')
    }
