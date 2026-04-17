# backend/lambda_function.py

import json
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]

table = dynamodb.Table(TABLE_NAME)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "OPTIONS":
        return response(200, {"message": "CORS OK"})

    try:
        if method == "POST" and path.endswith("/generate-upload-url"):
            return generate_upload_url(event)

        elif method == "GET" and path.endswith("/files"):
            return list_files()

        elif method == "DELETE" and "/files/" in path:
            return delete_file(event)

        else:
            return response(404, {"error": "Route not found"})
    except Exception as e:
        return response(500, {"error": str(e)})


def generate_upload_url(event):
    body = json.loads(event.get("body", "{}"))

    file_name = body.get("fileName")
    file_type = body.get("fileType", "application/octet-stream")

    if not file_name:
        return response(400, {"error": "fileName is required"})

    file_id = str(uuid.uuid4())
    safe_file_name = file_name.replace(" ", "_")
    s3_key = f"uploads/{file_id}_{safe_file_name}"

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
            "ContentType": file_type
        },
        ExpiresIn=300
    )

    file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

    item = {
        "id": file_id,
        "fileName": file_name,
        "s3Key": s3_key,
        "fileType": file_type,
        "uploadedAt": datetime.utcnow().isoformat(),
        "fileUrl": file_url
    }

    table.put_item(Item=item)

    return response(200, {
        "uploadUrl": upload_url,
        "fileId": file_id,
        "fileUrl": file_url
    })


def list_files():
    result = table.scan()
    items = result.get("Items", [])

    items.sort(key=lambda x: x.get("uploadedAt", ""), reverse=True)

    return response(200, items)


def delete_file(event):
    path_parameters = event.get("pathParameters") or {}
    file_id = path_parameters.get("id")

    if not file_id:
        return response(400, {"error": "file id is required"})

    result = table.get_item(Key={"id": file_id})
    item = result.get("Item")

    if not item:
        return response(404, {"error": "File not found"})

    s3.delete_object(Bucket=BUCKET_NAME, Key=item["s3Key"])
    table.delete_item(Key={"id": file_id})

    return response(200, {"message": "File deleted successfully"})
