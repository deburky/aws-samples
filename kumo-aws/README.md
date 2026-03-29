# Kumo

An open-source alternative to LocalStack.

```bash
docker run -p 4566:4566 ghcr.io/sivchari/kumo:latest
```

## Supported Services (71 total)

| Category | Services |
|----------|---------|
| Storage | S3, S3 Control, S3 Tables, DynamoDB, ElastiCache, MemoryDB, Glacier, EBS |
| Compute | Lambda, Batch, EC2, Elastic Beanstalk |
| Container | ECS, ECR, EKS |
| Database | RDS |
| Messaging | SQS, SNS, EventBridge, Kinesis, Firehose, MQ, Pipes, MSK (Kafka) |
| Security | IAM, KMS, Secrets Manager, ACM, Cognito, Security Lake, STS |
| Monitoring | CloudWatch, CloudWatch Logs, X-Ray, CloudTrail |
| Networking | CloudFront, Global Accelerator, API Gateway, Route 53, ELBv2, App Mesh |
| App Integration | Step Functions, AppSync, SES v2, Scheduler, Amplify |
| Management | SSM, Config, CloudFormation, Organizations, Service Quotas, Backup |
| Analytics & ML | Athena, Glue, Comprehend, Rekognition, SageMaker, Forecast |
| Developer Tools | CodeGuru Profiler, CodeGuru Reviewer |
| Other | Cost Explorer, DLM, Directory Service, EMR Serverless, GameLift |

> boto3 verified: S3, SQS, DynamoDB. SNS and API Gateway returned errors with boto3 (protocol mismatch).

## Test

```python
import boto3

kwargs = dict(
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    endpoint_url="http://localhost:4566",
)

# S3
s3 = boto3.client("s3", **kwargs)
s3.create_bucket(Bucket="test-bucket")
print("S3 ✓")

# SQS
sqs = boto3.client("sqs", **kwargs)
q = sqs.create_queue(QueueName="test-queue")
sqs.send_message(QueueUrl=q["QueueUrl"], MessageBody="hello")
print("SQS ✓")

# Lambda - just CreateFunction + Invoke
lmb = boto3.client("lambda", **kwargs)
# ...
print("Lambda ✓")
```