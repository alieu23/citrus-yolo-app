FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y mesa-libGL

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies (force wheels)
RUN pip install -r requirements.txt --no-cache-dir --only-binary=:all:

# Copy your model and code
COPY best.pt .
COPY handler.py .

# Lambda handler
CMD [ "handler.lambda_handler" ]

