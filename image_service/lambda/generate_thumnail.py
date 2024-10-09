import boto3
import os
from PIL import Image
import io

s3_client = boto3.client('s3')

def handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']

    for record in event['Records']:
        message = json.loads(record['body'])
        image_key = message['image_key']

        # Download the image from S3
        image_obj = s3_client.get_object(Bucket=bucket_name, Key=image_key)
        image = Image.open(io.BytesIO(image_obj['Body'].read()))

        # Generate the thumbnail
        image.thumbnail((100, 100))

        # Save the thumbnail back to S3
        thumbnail_key = image_key.replace("images/", "thumbnails/")
        buffer = io.BytesIO()
        image.save(buffer, 'JPEG')
        buffer.seek(0)

        s3_client.put_object(Bucket=bucket_name, Key=thumbnail_key, Body=buffer)

        print(f"Thumbnail created for {image_key}")
