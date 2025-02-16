import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from image_ops import get_image_obj
from models.llm import retrieve_claims_info, init_chat_obj
from repository.redis_repository import RedisRepository
from service.auth_service import AuthService
from service.aws_ocr import AwsOcrService
from service.ml_service import MlService
from service.aws_s3 import AwsS3Service
from service.rate_limit import RateLimitService

load_dotenv()

app = Flask(__name__)

app.config['AWS_REGION_NAME'] = os.getenv('AWS_REGION_NAME')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')

app.config['API_KEY'] = os.getenv('API_KEY')
app.config['REDIS_HOST'] = os.getenv('REDIS_HOST')
app.config['REDIS_PORT'] = os.getenv('REDIS_PORT')
app.config['REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD')
app.config['REDIS_DATABASE'] = os.getenv('REDIS_DATABASE')

aws_ocr = AwsOcrService()
ml_service = MlService()
aws_s3 = AwsS3Service()
auth_service = AuthService()
redis_repository = RedisRepository(app.config['REDIS_HOST'],
                                   app.config['REDIS_PORT'],
                                   app.config['REDIS_DATABASE'],
                                   app.config['REDIS_PASSWORD'],
                                   )

rate_limit_service = RateLimitService(redis_repository)
chat_obj = init_chat_obj()


@app.route('/ping')
def hello_world():
    return 'pong'


@app.route('/ocr', methods=['POST'])
def execute_aws_ocr():
    print(request.json)
    s3_file_path = ''

    path = request.json['image']
    if path is None or path == '':
        return jsonify({'message': 'No image path provided'})

    to_save = request.json['to_save']
    api_key = request.headers.get('API-Key')
    org_id = request.json['org_id']
    if org_id is None or org_id == '':
        return jsonify({'message': 'No Organization provided'})

    staff_id = request.json['staff_id']
    if staff_id is None or staff_id == '':
        return jsonify({'message': 'No Staff ID provided'})

    is_valid_api_key = auth_service.validate_api_key(api_key)
    if not is_valid_api_key:
        is_org_limit_exceed = rate_limit_service.validate_org_limit_exceed(org_id)
        if is_org_limit_exceed:
            return jsonify({'message': 'Organization Maximum limit exceeded'})

        is_staff_limit_exceed = rate_limit_service.validate_staff_limit(staff_id)
        if is_staff_limit_exceed:
            return jsonify({'message': 'Staff Maximum limit exceeded'})

        rate_limit_service.count_organization_request(org_id, 1)
        rate_limit_service.count_staff_request(staff_id, 1)

    response = aws_ocr.detect_file_text(path)
    if to_save:
        image_binary = get_image_obj(path, 'filepath', 'binary')
        s3_file_path = aws_s3.save_image(path, image_binary)

    return jsonify({
        's3_file_path': s3_file_path,
        'data': response
    })


# Give a S3 filepath of the claims receipt, and run OCR + LLM on it to produce result we need
@app.route('/claims_model', methods=['POST'])
def execute_claims_model():
    s3_file_path = request.json['s3_file_path']

    if not s3_file_path:
        return jsonify({'message': 'No S3 file path provided'})

    print("S3 file: " + s3_file_path)
    claims_result, api_response, _, actual_output = retrieve_claims_info(chat_obj, s3_file_path)

    return jsonify({
        'result': claims_result,
        'actual_output': actual_output
    })


@app.route('/ocr_pdf', methods=['POST'])
def execute_aws_ocr_pdf():
    s3_bucket = request.json['s3_bucket']
    s3_file_path = request.json['s3_file_path']

    response = aws_ocr.detect_from_pdf_file(s3_bucket, s3_file_path)

    return jsonify(response)


@app.route('/ml', methods=['POST'])
def execute_aws_ml():
    result = ml_service.placeholder_function()

    return jsonify({
        'statusCode': 200,
        'result': result
    })


@app.route('/set_hash_key', methods=['POST'])
def set_hash_key():
    hash_key = request.json['hash_key']
    key = request.json['key']
    value = request.json['value']

    redis_repository.set_hash_key(hash_key, key, value)

    return jsonify({
        'value': redis_repository.get_hash_key(hash_key, key)
    })


@app.route('/set_key', methods=['POST'])
def set_key():
    key = request.json['key']
    value = request.json['value']

    redis_repository.set_key(key, value)

    return jsonify({
        'value': redis_repository.get_key(key)
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
