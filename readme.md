## CitrusInsight: Automated Orchard Yield Estimation

CitrusInsight is an end-to-end, cloud-native computer vision pipeline designed to solve the challenge of manual fruit counting in large-scale orchards. By leveraging deep learning (YOLOv11) and serverless cloud architecture, it provides growers with a scalable, cost-effective tool for estimating harvest yields from digital imagery.

## System Architecture
The system is built using a decoupled, event-driven architecture to handle high-volume image processing without server degradation.
- **Frontend:** React.js (Vite) single-page application.
- **API Gateway:** AWS Lambda Function URL running a Dockerized FastAPI application.
- **Inference Engine:** AWS SageMaker Real-Time Endpoint hosting a YOLOv11 model.
- **Storage:**
  - **Amazon S3:** Dual-bucket system for raw-input and annotated-results.
  - **Amazon DynamoDB:** NoSQL metadata storage using composite keys (BatchID#FileName) for session-based grouping.

## Key Features
- **Intelligent Batch Processing:** Frontend logic chunks folder uploads (5 images at a time) to respect AWS concurrency limits and prevent 429 Too Many Requests errors.
- **Real-time Annotation:** Backend OpenCV integration draws bounding boxes and confidence scores directly on images before storage.
- **Yield History:** Aggregated dashboard allowing users to view total counts and processed images grouped by their unique upload session.
- **Cost Optimization:** Dedicated CLI scripts to "Sleep" (destroy) and "Wake" (re-deploy) the SageMaker inference engine to minimize hourly compute costs.

## Tech Stack
Component ==============Technology
Model==============Ultralytics YOLOv11 (PyTorch)
Backend==============="Python 3.11, FastAPI, Mangum, OpenCV"
Infrastructure==============="Docker, AWS Lambda, SageMaker, S3, DynamoDB"
Frontend===================="React, Tailwind CSS, Axios, Lucide"

## Configuration & Deployment
### 1. Backend Environment Variables
Ensure the following variables are set in the AWS Lambda Console:
- DYNAMODB_TABLE: OrchardYieldMetadata
- SAGEMAKER_ENDPOINT: CitrusYieldEndpoint
- RAW_BUCKET: orchard-input-raw
- RESULT_BUCKET: orchard-results-annotated

## Docker Build
- **Build Image:** docker build --platform linux/amd64 -t citrus-backend-lambda -f Dockerfile.backend . 
- **Tag Image:** docker tag citrus-backend-lambda:latest [your_id].dkr.ecr.us-east-2.amazonaws.com/citrus-backend-lambda:latest
- **Push Image:** docker push 074172988430.dkr.ecr.us-east-2.amazonaws.com/citrus-backend-lambda:latest