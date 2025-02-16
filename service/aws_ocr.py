import boto3
from flask import current_app
from image_ops import get_image_obj


class AwsOcrService:

    def detect_file_text(self, image_path: str):
        textract = boto3.client('textract',
                                region_name=current_app.config['AWS_REGION_NAME'],
                                aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                                aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
                                )
        input_type = 'filepath' if 'telegram' in image_path else 'blob'

        image_binary = get_image_obj(image_path, input_type, 'binary')

        response = textract.detect_document_text(Document={'Bytes': image_binary})

        return response

    def detect_from_s3_file(self, s3_file_path: str):
        textract = boto3.client('textract',
                                region_name=current_app.config['AWS_REGION_NAME'],
                                aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                                aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
                                )

        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': s3_file_path.split('/')[2],
                    'Name': '/'.join(s3_file_path.split('/')[3:])
                }
            }
        )

        # file_content = ''
        # for item in response['Blocks']:
        #     if item['BlockType'] == 'LINE':
        #         file_content += item['Text'] + '\n'

        return response

    def detect_from_pdf_file(self, s3_bucket: str, pdf_file_path: str):
        textract = boto3.client('textract',
                                region_name=current_app.config['AWS_REGION_NAME'],
                                aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                                aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
                                )

        response = textract.detect_document_text(Document={
            'S3Object': {
                'Bucket': s3_bucket,
                'Name': pdf_file_path
            }
        })

        return response
