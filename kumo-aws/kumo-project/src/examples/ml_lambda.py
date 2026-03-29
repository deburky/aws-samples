import json


def simple_prediction(features):
    """A simple prediction function"""
    # Just multiply and sum the features for demonstration
    return sum(x * i for i, x in enumerate(features, 1))


def lambda_handler(event, context):
    """
    Lambda function that makes predictions using a simple function
    Input event should contain 'features' key with list of 4 numbers
    """
    try:
        # Get features from the event or use default
        features = event.get("features", [1.0, 2.0, 3.0, 4.0])

        # Make prediction
        prediction = simple_prediction(features)

        return {
            "statusCode": 200,
            "body": json.dumps({"prediction": prediction, "features": features}),
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


if __name__ == "__main__":
    # Local test
    test_event = {"features": [1.0, 2.0, 3.0, 4.0]}
    result = lambda_handler(test_event, None)
    print(f"Test prediction result: {result}")
