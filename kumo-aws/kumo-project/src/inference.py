import json

import joblib
import numpy as np

# Load pre-trained models (loaded once when Lambda initializes)
scaler = joblib.load("scaler.pkl")
outlier_detector = joblib.load("model.pkl")


def handler(event, context):  # pylint: disable=unused-argument
    """
    Lambda handler that makes predictions using a simple function
    Input event should contain 'features' key with list of 4 numbers
    """
    try:
        # Parse input data
        body = json.loads(event["body"])
        features = body.get("features", [])

        # Data validation
        if not features or not isinstance(features, list):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Invalid input: features must be a non-empty array"}
                ),
            }

        # ML processing
        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(
            features_array
        )  # Use transform (not fit_transform)
        is_outlier = (
            outlier_detector.predict(features_scaled)[0] == -1
        )  # Use predict on scaled data (not fit_predict)

        # Calculate feature importance
        abs_features = np.abs(features_array[0])
        feature_importance = abs_features / (np.sum(abs_features) + 1e-10)

        # Generate prediction response
        prediction = {
            "base_prediction": float(np.mean(features_scaled) * 10),
            "confidence": float(1.0 / (1.0 + np.std(features_scaled))),
            "feature_importance": [float(x) for x in feature_importance],
            "is_anomaly": bool(is_outlier),
            "stats": {
                "mean": float(np.mean(features)),
                "std": float(np.std(features)),
                "min": float(np.min(features)),
                "max": float(np.max(features)),
            },
        }

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "prediction": prediction,
                    "features": features,
                    "features_scaled": features_scaled.tolist()[0],
                }
            ),
        }

    except json.JSONDecodeError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid JSON: {str(e)}"}),
        }
    except (KeyError, ValueError, TypeError) as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid input: {str(e)}"}),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
