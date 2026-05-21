# AWS Samples

A personal collection of AWS samples demonstrating local development with AWS services.

Authored by: [Denis Burakov](https://github.com/deburky)

## Projects

### [kumo-aws](./kumo-aws)

An ML prediction service built with [Kumo](https://github.com/sivchari/kumo) — a lightweight, open-source AWS emulator (32 MB Docker container, no AWS account required).

**Features:**
- REST prediction API (IsolationForest anomaly detection via scikit-learn)
- AWS Lambda containerized function deployed via AWS SAM
- Local AWS service emulation (S3, SQS, DynamoDB, STS, IAM, API Gateway, and 66+ more)
- `KumoSession` boto3 compatibility layer for seamless Kumo integration
- Pre-commit hooks, GitHub Actions CI/CD, and pytest integration tests

**Quick start:**

```bash
cd kumo-aws/kumo-project
make start        # Start Kumo, train models, build & deploy Lambda
make test-endpoint # POST to http://127.0.0.1:3000/predict
make stop         # Tear down all services
```

**Tech stack:** Python, scikit-learn, AWS SAM, Docker, boto3, pytest

### [appconfig_agent](./appconfig_agent)

A generic Python package that ports AWS AppConfig Agent behavior:
- Fetches raw configuration through the AppConfig management API
- Evaluates variant/rule expressions locally for feature-flag resolution
- Includes cache + backup fallback logic for resilient reads

**Tech stack:** Python, boto3

### [bedrock-claude](./bedrock-claude)

A self-service Text2SQL demo that lets non-technical users query a Redshift data warehouse in plain English.

**How it works:**
- User types a question in the browser
- Claude Code generates a read-only SQL query and executes it via the Redshift Data API
- Results are returned and summarized directly in the terminal

**Features:**
- Marimo web app with embedded Claude Code terminal (via ttyd + xterm.js)
- Redshift Data API — no VPN, no direct DB connection required
- Dockerfile for EC2 deployment; AWS credentials via IAM role
- No credentials in code — `.env` and `claude-launch.sh` are gitignored

**Quick start:**

```bash
cd bedrock-claude
cp .env.example .env          # fill in Redshift vars
cp claude-launch.sh.example claude-launch.sh  # fill in same vars
uv venv app/.venv && uv pip install --python app/.venv marimo boto3 python-dotenv pandas
ttyd -p 7681 -W ./claude-launch.sh &
marimo run app/text2sql.py --port 2718
```

**Tech stack:** Python, Marimo, Claude Code, Redshift Data API, boto3, ttyd, Docker
