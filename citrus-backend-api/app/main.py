import io
import os
import json
import boto3
import cv2
import numpy as np
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(title="CitrusInsight API")

# AWS Clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sm_runtime = boto3.client("sagemaker-runtime", region_name="us-east-2")

# Constants
TABLE = dynamodb.Table('OrchardYieldMetadata')
RAW_BUCKET = "orchard-input-raw"
ANNOTATED_BUCKET = "orchard-results-annotated"
ENDPOINT_NAME = "CitrusYieldEndpoint"


@app.get("/")
async def root():
    return {
        "message": "CitrusInsight API is Online",
        "version": "1.1.0",
        "region": "us-east-2"
    }


@app.get("/health")
async def health_check():
    try:
        s3.list_objects_v2(Bucket=RAW_BUCKET, MaxKeys=1)
        TABLE.table_status
        return {"status": "healthy", "aws_connectivity": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/analyze")
async def analyze_image(
        file: UploadFile = File(...),
        batch_id: str = Form(...)  # Explicitly defined as Form to avoid value_errors
):
    timestamp_str = datetime.now().isoformat()
    filename = file.filename

    try:
        # 1. Read Image Bytes
        image_bytes = await file.read()

        # 2. Upload Raw Image to S3 (Organized by Batch)
        s3.put_object(Bucket=RAW_BUCKET, Key=f"{batch_id}/{filename}", Body=image_bytes)

        # 3. Call SageMaker for YOLOv11 Inference
        response = sm_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/x-image",
            Body=image_bytes
        )
        prediction = json.loads(response['Body'].read().decode())

        count = prediction.get("count", 0)
        boxes = prediction.get("predictions", [])

        # 4. Annotate Image using OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        for pred in boxes:
            box = pred['box']
            cv2.rectangle(img, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 165, 255), 3)
            cv2.putText(img, f"Orange: {pred['score']:.2f}", (int(box[0]), int(box[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)

        # 5. Upload Annotated Image to S3
        _, buffer = cv2.imencode(".jpg", img)
        annotated_key = f"{batch_id}/annotated_{filename}"
        s3.put_object(
            Bucket=ANNOTATED_BUCKET,
            Key=annotated_key,
            Body=buffer.tobytes(),
            ContentType="image/jpeg"
        )

        # 6. Write Metadata to DynamoDB
        result_url = f"https://{ANNOTATED_BUCKET}.s3.us-east-2.amazonaws.com/{annotated_key}"

        confidence_value = float(boxes[0]['score']) if boxes else 0.0
        # Use a composite key for MediaID (BatchID + Filename) to prevent overwrites
        TABLE.put_item(Item={
            'MediaID': f"{batch_id}#{filename}",
            'BatchID': batch_id,
            'FileName': filename,
            'Count': int(count), # Ensure this is a standard Python int
            'Confidence': str(round(confidence_value, 2)),
            'Timestamp': timestamp_str,
            'ResultURL': result_url
        })

        return {
            "filename": filename,
            "count": count,
            "result_url": result_url,
            "timestamp": timestamp_str
        }

    except Exception as e:
        print(f"Error in /analyze: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batches")
async def get_batches():
    try:
        # Scan using placeholders for reserved keywords 'Count' and 'Timestamp'
        response = TABLE.scan(
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

            # We MUST cast them to int/float for the React UI to read them.
            count = int(item.get('Count', 0))
            ts = item.get('Timestamp', '')
            url = item.get('ResultURL', '')

            if bid not in batches_map:
                batches_map[bid] = {
                    "batchId": bid,
                    "totalYield": 0,
                    "fileCount": 0,
                    "createdAt": ts,
                    "thumbnail": url  # First image found becomes the folder preview
                }

            batches_map[bid]["totalYield"] += count
            batches_map[bid]["fileCount"] += 1

            # Keep the earliest timestamp as the batch creation date
            if ts < batches_map[bid]["createdAt"]:
                batches_map[bid]["createdAt"] = ts

        # Convert to list and sort by Newest first
        history = list(batches_map.values())
        history.sort(key=lambda x: x['createdAt'], reverse=True)

        return history

    except Exception as e:
        print(f"Error in /batches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Lambda Handler
handler = Mangum(app)