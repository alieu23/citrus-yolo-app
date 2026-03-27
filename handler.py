import json
import os
import boto3
import cv2
from ultralytics import YOLO
from datetime import datetime
import datetime

# Initialize AWS Clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('OrchardYieldMetadata')

# 1. Load Model from S3 or local /tmp
# In a container, best.pt is usually baked into the image.
model = YOLO('/var/task/best.pt')
timestamp_str = datetime.datetime.now().isoformat()

def lambda_handler(event, context):
    # 2. Get Bucket and Key from S3 Event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    download_path = f'/tmp/{os.path.basename(key)}'
    upload_path = f'/tmp/annotated_{os.path.basename(key)}'

    # 3. Download the file for processing
    s3.download_file(bucket, key, download_path)

    # 4. Run Inference with Tracking
    # We use imgsz=1024 to catch background oranges
    results = model.predict(download_path, imgsz=1024, conf=0.38, verbose=False)

    # 5. Extract Metadata
    boxes = results[0].boxes
    count = len(boxes)
    track_ids = boxes.id.int().cpu().tolist() if boxes.id is not None else []
    avg_conf = float(boxes.conf.mean()) if len(boxes) > 0 else 0

    # 6. Save Annotated Visual
    annotated_frame = results[0].plot()
    cv2.imwrite(upload_path, annotated_frame)

    results_bucket = "orchard-results-annotated"
    s3.upload_file(upload_path, results_bucket, f"annotated_{key}")


    # 7. Write to DynamoDB
    table.put_item(Item={
        'MediaID': key,
        'Timestamp': timestamp_str,
        'Count': count,
        'Confidence': str(round(avg_conf, 2)),
        'TrackIDs': track_ids,
        'ResultURL': f"https://{results_bucket}.s3.amazonaws.com/annotated_{key}"
    })

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed {key}. Detected {count} oranges.')
    }