import os
import boto3
import json
from dotenv import load_dotenv
import zipfile
import io

load_dotenv()


def get_lambda_client():
    return boto3.client(
        "lambda",
        endpoint_url=os.getenv("ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )


def create_zip_package(script_path):
    """Create a ZIP file containing the Lambda function code"""
    zip_output = io.BytesIO()
    with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add the main Lambda function
        zipf.write(script_path, "ml_lambda.py")

    zip_output.seek(0)
    return zip_output.read()


def deploy_lambda():
    """Deploy the ML Lambda function to LocalStack"""
    lambda_client = get_lambda_client()

    # Create a ZIP package of our Lambda function
    zip_file = create_zip_package("src/examples/ml_lambda.py")

    try:
        # Create the Lambda function
        response = lambda_client.create_function(
            FunctionName="MLPredictionFunction",
            Runtime="python3.9",
            Role="arn:aws:iam::000000000000:role/lambda-role",  # Dummy role for LocalStack
            Handler="ml_lambda.lambda_handler",
            Code={"ZipFile": zip_file},
            Timeout=30,
            MemorySize=256,
            Environment={"Variables": {"PYTHONPATH": "/var/task"}},
        )

        print(f"Created Lambda function: {response['FunctionName']}")
        return response["FunctionArn"]

    except lambda_client.exceptions.ResourceConflictException:
        print("Function already exists, updating code...")

        # Update existing function
        response = lambda_client.update_function_code(
            FunctionName="MLPredictionFunction", ZipFile=zip_file
        )

        print(f"Updated Lambda function: {response['FunctionName']}")
        return response["FunctionArn"]


def invoke_lambda(features):
    """Invoke the Lambda function with test data"""
    lambda_client = get_lambda_client()

    # Prepare test event
    test_event = {"features": features}

    try:
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName="MLPredictionFunction",
            InvocationType="RequestResponse",
            Payload=json.dumps(test_event),
        )

        # Read the response
        result = json.loads(response["Payload"].read())
        print("\nLambda function response:")
        print(json.dumps(result, indent=2))

        return result

    except Exception as e:
        print(f"Error invoking Lambda: {str(e)}")
        return None


if __name__ == "__main__":
    # Deploy the Lambda function
    function_arn = deploy_lambda()
    print(f"\nFunction ARN: {function_arn}")

    # Test the function with sample data
    test_features = [1.0, 2.0, 3.0, 4.0]
    result = invoke_lambda(test_features)

    if result and result.get("statusCode") == 200:
        body = json.loads(result["body"])
        print(f"\nPrediction for features {body['features']}: {body['prediction']}")
