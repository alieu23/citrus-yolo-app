import sagemaker
from sagemaker.pytorch import PyTorchModel

# Replace with your actual Role ARN from IAM
#role = "arn:aws:iam::074172988430:role/service-role/AmazonSageMaker-ExecutionRole"
role = "arn:aws:iam::074172988430:role/sageMakeAccessRole"

pytorch_model = PyTorchModel(
    model_data="s3://sagemaker-citrus-model/model.tar.gz", # Upload your tar.gz here first
    role=role,
    entry_point='inference.py',
    source_dir='citrus-model/code',
    framework_version='2.0',
    py_version='py310'
)

predictor = pytorch_model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.xlarge',
    endpoint_name="CitrusYieldEndpoint"
)
print("Endpoint is Live!")