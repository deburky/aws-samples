"""
Train and save ML models for the prediction service.
Run this script to generate model.pkl and scaler.pkl files.
"""

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def train_and_save_models():
    """Train models on sample data and save them."""
    print("Training ML models...")

    # Generate sample training data
    # In production, this would be your actual training dataset
    np.random.seed(42)
    n_samples = 1000
    n_features = 4

    # Generate normal data
    X_train = np.random.randn(n_samples, n_features) * 2 + 5

    # Add some outliers
    n_outliers = int(n_samples * 0.1)
    X_outliers = np.random.uniform(-10, 20, size=(n_outliers, n_features))
    X_train = np.vstack([X_train, X_outliers])

    print(f"Training data shape: {X_train.shape}")

    # Train scaler
    print("Training StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train outlier detector on scaled data
    print("Training IsolationForest...")
    outlier_detector = IsolationForest(
        contamination=0.1, random_state=42, n_estimators=100
    )
    outlier_detector.fit(X_train_scaled)

    # Save models
    print("Saving models...")
    joblib.dump(scaler, "scaler.pkl")
    joblib.dump(outlier_detector, "model.pkl")

    print("Models saved successfully.")

    # Test the saved models
    print("\nTesting saved models...")
    loaded_scaler = joblib.load("scaler.pkl")
    loaded_model = joblib.load("model.pkl")

    # Test with sample data (should be normal)
    test_data = np.array([[1.0, 2.0, 3.0, 4.0]])
    test_data_scaled = loaded_scaler.transform(test_data)
    prediction = loaded_model.predict(test_data_scaled)

    print(f"Test prediction: {'Normal' if prediction[0] == 1 else 'Anomaly'}")
    print("Models loaded and working correctly.")


if __name__ == "__main__":
    train_and_save_models()
