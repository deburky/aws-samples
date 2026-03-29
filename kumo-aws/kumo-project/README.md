# ML Prediction Service with Kumo and SAM

This project demonstrates how to set up a machine learning prediction service using [Kumo](https://github.com/sivchari/kumo) for local AWS service emulation and SAM (Serverless Application Model) for local Lambda development. The service exposes a REST API endpoint that accepts feature data and returns predictions using pre-trained scikit-learn models.

## Project Structure

```
kumo-project/
├── src/
│   ├── train.py              # Script to train and save ML models
│   ├── inference.py          # Lambda function for predictions
│   ├── kumo_compat.py        # KumoSession: boto3 compatibility wrapper
│   ├── Dockerfile            # Container definition for Lambda
│   ├── requirements.txt      # Lambda Python dependencies
│   ├── model.pkl             # Pre-trained outlier detection model (generated)
│   └── scaler.pkl            # Pre-trained feature scaler (generated)
├── src/examples/
│   ├── s3_operations.py      # S3 example using KumoSession
│   └── sts_example.py        # STS/IAM assume-role example using KumoSession
├── tests/
│   └── test_s3_operations.py
├── .github/
│   └── workflows/
│       └── deploy-and-test.yml
├── template.yaml             # SAM template
├── Makefile                  # Build and utility commands
└── docker-compose.yml        # Kumo configuration
```

## Prerequisites

### Required

1. **Docker Desktop** (or Docker Engine + Docker Compose)
   - **Installation**: macOS: `brew install --cask docker`
   - **Verify**: `docker --version && docker-compose --version`

2. **AWS SAM CLI**
   - **Installation**: macOS: `brew install aws-sam-cli`
   - **Verify**: `sam --version`

3. **Python 3.12+**
   - **Verify**: `python3 --version`

4. **uv** (recommended for dependency management)
   - **Installation**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - **Verify**: `uv --version`

### Quick Prerequisites Check

```bash
docker --version && docker ps
sam --version
python3 --version
```

## Quick Start

```bash
# 1. Install dependencies
make install

# 2. Start Kumo, train models, build, and test
make start
```

`make start` will:
1. Start Kumo (if not running)
2. Train ML models
3. Build the SAM application with Docker
4. Start the local API on `http://127.0.0.1:3000`
5. Run a test prediction

## Available Make Commands

```
make install       - Install Python dependencies
make train-models  - Train and save ML models
make start         - Start Kumo and deploy the service
make stop          - Stop Kumo and SAM API
make restart       - Restart Kumo and redeploy
make build         - Build SAM application
make test-endpoint - Quick test of the prediction endpoint
make clean         - Clean up everything
```

## Kumo

[Kumo](https://github.com/sivchari/kumo) is a lightweight, MIT-licensed AWS emulator written in Go. It runs as a 32MB Docker container, requires no account or token, and listens on port 4566 — the same default as LocalStack.

```bash
docker run -p 4566:4566 ghcr.io/sivchari/kumo:latest
```

### boto3 Compatibility

Kumo has two quirks compared to LocalStack that `KumoSession` (`src/kumo_compat.py`) handles transparently:

- **Query-protocol services** (STS, IAM, RDS, ...): Kumo strict-matches `application/x-www-form-urlencoded` without the `; charset=utf-8` suffix that boto3 appends, causing `MissingTargetHeader` errors. `KumoSession` registers a `before-send` hook to strip the suffix.
- **Path prefixes**: Some services are routed under non-root paths (IAM at `/iam/`, API Gateway at `/apigateway/`). `KumoSession` applies the correct prefix per service automatically.

Usage:

```python
from src.kumo_compat import KumoSession

session = KumoSession()
s3  = session.client("s3")   # standard endpoint
iam = session.client("iam")  # /iam prefix + charset hook applied
sts = session.client("sts")  # charset hook applied
```

## Testing the API

### Quick Test

```bash
make test-endpoint
```

### Manual Test

```bash
curl -X POST "http://127.0.0.1:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0, 4.0]}'
```

### Example Response

```json
{
  "prediction": {
    "base_prediction": -7.846485258771873,
    "confidence": 0.7292884072848042,
    "feature_importance": [0.1, 0.2, 0.3, 0.4],
    "is_anomaly": false,
    "stats": {
      "mean": 2.5,
      "std": 1.118033988749895,
      "min": 1.0,
      "max": 4.0
    }
  },
  "features": [1.0, 2.0, 3.0, 4.0],
  "features_scaled": [-1.305, -0.909, -0.631, -0.293]
}
```

### Testing Anomaly Detection

```bash
curl -X POST "http://127.0.0.1:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features": [100.0, 200.0, 300.0, 400.0]}'
```

The response will show `"is_anomaly": true`.

## ML Models

- **Outlier Detection**: IsolationForest (10% contamination, 100 estimators)
- **Feature Scaling**: StandardScaler fitted on synthetic training data
- **Training Data**: 1000 samples with 4 features

Models are trained once and loaded at Lambda startup (cold start optimization). Run `make train-models` to regenerate them.

## Troubleshooting

**Models not loading in Lambda**
```bash
make clean
make start   # train-models runs automatically before build
```

**Port already in use**
```bash
lsof -i :3000
kill -9 <PID>
```

**Kumo not starting**
```bash
docker ps
docker-compose up -d
```

## License

MIT
