import boto3
import json
import os
from decimal import Decimal

# Initialize clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sm_runtime = boto3.client("sagemaker-runtime", region_name="us-east-2")

# Constants
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "OrchardYieldMetadata")
ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT", "CitrusYieldEndpoint")


def upload_to_s3(bucket, key, body, content_type="image/jpeg"):
    """Handles all S3 uploads (Raw and Annotated)"""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type
    )
    # Return the public URL
    return f"https://{bucket}.s3.us-east-2.amazonaws.com/{key}"


def call_sagemaker_yolo(image_bytes):
    """Sends image to SageMaker and returns parsed JSON"""
    response = sm_runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/x-image",
        Body=image_bytes
    )
    # SageMaker returns floats; json.loads handles them well
    return json.loads(response['Body'].read().decode())


def save_metadata_to_db(item):
    """Writes the final analysis results to DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)

    # Ensure all numeric values are cast to types DynamoDB likes (int/Decimal)
    # But for storing, standard Python ints work fine with boto3
    return table.put_item(Item=item)


def get_batch_history():
    """Scans DynamoDB and aggregates data by BatchID for the UI"""
    table = dynamodb.Table(TABLE_NAME)

    # Use ExpressionAttributeNames for reserved words 'Count' and 'Timestamp'
    response = table.scan(
        ProjectionExpression="BatchID, #c, #ts, ResultURL",
        ExpressionAttributeNames={
            "#c": "Count",
            "#ts": "Timestamp"
        }
    )
    items = response.get('Items', [])

    batches_map = {}

    for item in items:
        bid = item.get('BatchID', 'Uncategorized')

        # FIX: Explicitly cast Decimal from DynamoDB to Python types
        # This prevents the "Object of type Decimal is not JSON serializable" error
        count = int(item.get('Count', 0))
        timestamp = str(item.get('Timestamp', ''))
        image_url = str(item.get('ResultURL', ''))

        if bid not in batches_map:
            batches_map[bid] = {
                "batchId": bid,
                "totalYield": 0,
                "fileCount": 0,
                "createdAt": timestamp,
                "thumbnail": image_url
            }

        batches_map[bid]["totalYield"] += count
        batches_map[bid]["fileCount"] += 1

        # Ensure we keep the earliest timestamp as the 'Created' date
        if timestamp < batches_map[bid]["createdAt"]:
            batches_map[bid]["createdAt"] = timestamp

    # Sort by newest first
    sorted_history = list(batches_map.values())
    sorted_history.sort(key=lambda x: x['createdAt'], reverse=True)

    return sorted_history