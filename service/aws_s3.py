import uuid
import boto3

from flask import current_app

from image_ops import get_extension


class AwsS3Service:

    def save_image(self, path, image):
        s3_client = boto3.client('s3',
                                 region_name=current_app.config['AWS_REGION_NAME'],
                                 aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                                 aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
                                 )

        bucket_name = 'my-bucket'
        extension = get_extension(path)
        file_name = str(uuid.uuid4()) + extension

        try:
            s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=image)
            print(f"Upload to {bucket_name} successful: {file_name}")
            return f"s3://{bucket_name}/{file_name}"

        except Exception as e:
            print(f"Upload failed to bucket-name: {bucket_name} with file-name: {file_name} with error: {e}")
            return None
