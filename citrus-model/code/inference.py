import os
import io
import json
import numpy as np
from ultralytics import YOLO
from PIL import Image

# Force YOLO to use a writable directory for its internal settings
os.environ['YOLO_CONFIG_DIR'] = '/tmp'


def model_fn(model_dir):
    """Loads the YOLOv11 model from the model_dir."""
    model_path = os.path.join(model_dir, "best.pt")
    if not os.path.exists(model_path):
        # Listing directory helps debug if model.tar.gz structure is wrong
        print(f"DEBUG: Contents of {model_dir}: {os.listdir(model_dir)}")
        raise FileNotFoundError(f"Model file 'best.pt' not found at {model_path}")

    return YOLO(model_path)


def input_fn(request_body, request_content_type):
    """De-serializes the incoming image bytes."""
    # .strip() handles cases where headers might have extra whitespace
    if request_content_type.strip() == "application/x-image":
        return Image.open(io.BytesIO(request_body))
    raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """Performs inference and formats numbers for JSON compatibility."""
    results = model(input_data)
    predictions = []

    for r in results:
        for box in r.boxes:
            # We explicitly cast to float/int to prevent 'Object not JSON serializable' errors
            # Changed 'class' to 'class_id' to match Detection schema in schemas.py
            predictions.append({
                "box": [float(x) for x in box.xyxy[0].tolist()],
                "score": round(float(box.conf[0]), 4),
                "class_id": int(box.cls[0])
            })

    return {
        "count": len(predictions),
        "predictions": predictions
    }


def output_fn(prediction, content_type):
    """Serializes the prediction dictionary into a JSON string."""
    # Using a custom separator or ensuring standard types for maximum compatibility
    return json.dumps(prediction), "application/json"