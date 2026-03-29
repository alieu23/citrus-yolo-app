from pydantic import BaseModel
from typing import List, Optional

# 1. This defines a single orange detection from YOLO
class Detection(BaseModel):
    box: List[float]  # [xmin, ymin, xmax, ymax]
    score: float      # Confidence (0.0 to 1.0)
    class_id: Optional[int] = 0 # Default to 0 for Oranges

# 2. This is the "Contract" for the /analyze endpoint response
class AnalysisResponse(BaseModel):
    filename: str
    count: int
    result_url: str
    timestamp: str
    # We include predictions as an optional list in case the UI needs the raw boxes
    predictions: Optional[List[Detection]] = []

# 3. This defines what a "Batch Folder" looks like in the History tab
class BatchSummary(BaseModel):
    batchId: str
    totalYield: int
    fileCount: int
    createdAt: str
    thumbnail: str

# 4. Standard Error schema for FastAPI
class ErrorResponse(BaseModel):
    detail: str