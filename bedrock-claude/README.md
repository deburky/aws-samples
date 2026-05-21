# Text2SQL with Claude on AWS Bedrock

Self-serve BI tool: ask questions in plain English, get SQL + results from Redshift.

## Architecture

```
User question (natural language)
        │
        ▼
Claude via AWS Bedrock (generates SQL)
        │
        ▼
Redshift Data API (executes read-only query)
        │
        ▼
Results returned to user
```

**Two interfaces:**

| Path | For whom | How it works |
|------|----------|--------------|
| **Claude Code + Skill** (`skills/`) | Power users (terminal) | Claude Code reads the skill, writes SQL, executes via Data API |
| **Marimo Web App** (`app/`) | Product colleagues (browser) | Web UI chat → Claude generates SQL → Data API → results in table |

## Security & Data Residency

- All traffic stays within AWS (your region)
- AWS does not train on your data (Bedrock contractual guarantee)
- Every `InvokeModel` call logged in **CloudTrail** (IAM principal, timestamp, model ID)
- Redshift access is read-only, scoped to the configured `DbUser`
- No API keys — authentication via IAM credentials

## What IT Needs to Provision

1. **Bedrock model access** enabled for `anthropic.claude-*` in your AWS account/region
2. **IAM role** — deploy the CloudFormation template in `iam/text2sql-role.yaml`:
   ```bash
   aws cloudformation deploy \
     --template-file iam/text2sql-role.yaml \
     --stack-name text2sql-iam \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
       RedshiftClusterIdentifier=my-cluster \
       RedshiftDatabaseName=my_db \
       RedshiftDbUser=readonly_user \
       BedrockRegion=eu-west-1
   ```
   This creates a role with exactly these permissions:
   - `bedrock:InvokeModel` (scoped to `anthropic.claude-*`)
   - `redshift-data:ExecuteStatement`, `DescribeStatement`, `GetStatementResult`
   - `redshift:GetClusterCredentials` (scoped to the specific cluster/user/db)
3. **Redshift cluster** with a read-only `DbUser` for the product team

## Quick Start

### Option A: Claude Code (local CLI)

```bash
# 1. Configure AWS credentials
aws configure --profile your-profile
export AWS_PROFILE=your-profile

# 2. Set Redshift env vars
export REDSHIFT_REGION=eu-west-1  # Ireland
export REDSHIFT_HOST=your-cluster.xxxx.eu-west-1.redshift.amazonaws.com
export REDSHIFT_DB_NAME=your_db
export REDSHIFT_USER_NAME=readonly_user

# 3. Copy the skill into Claude Code
cp -r skills/redshift-data-api ~/.claude/skills/

# 4. Configure Claude Code to use Bedrock
claude config set apiProvider bedrock

# 5. Ask questions
claude "How many active customers do we have by country?"
```

### Option B: Marimo Web App

```bash
# 1. Set environment variables (same as above, plus):
export AWS_DEFAULT_REGION=eu-west-1

# 2. Run the app
cd app
marimo run text2sql.py

# 3. Open http://localhost:2718 in your browser
```

### Deployment (EC2 / App Runner)

```bash
# Build and run with Docker
cd app
docker build -t text2sql .
docker run -p 2718:2718 \
  -e REDSHIFT_REGION=eu-west-1 \  # Ireland
  -e REDSHIFT_HOST=your-cluster.xxxx.eu-west-1.redshift.amazonaws.com \
  -e REDSHIFT_DB_NAME=your_db \
  -e REDSHIFT_USER_NAME=readonly_user \
  text2sql
```

On EC2, attach an IAM instance profile with the permissions above — no keys needed.
For App Runner, configure the IAM role in the service settings.

## Project Structure

```
bedrock-claude/
├── README.md
├── iam/
│   └── text2sql-role.yaml    # CloudFormation — IAM role for IT to deploy
├── skills/
│   └── redshift-data-api/
│       ├── SKILL.md          # Claude Code skill definition
│       └── helper.py         # Redshift Data API helper (pagination, null handling)
└── app/
    ├── text2sql.py           # Marimo text2sql app (main)
    ├── app.py                # Marimo general chat app (Bedrock)
    ├── db.py                 # Redshift Data API query executor
    ├── example.py            # Minimal Bedrock SDK example
    ├── Dockerfile            # Container deployment
    ├── marimo.toml           # Marimo config
    └── schema/
        ├── schema.sql        # Sample table definitions
        ├── seed.sql          # Sample data
        └── schema_context.md # Schema reference for Claude
```

## Redshift Serverless (Free Trial)

AWS offers a **$300 credit for 3 months** for Redshift Serverless — enough for demo and evaluation.
Enable it in the AWS console under Amazon Redshift > Serverless.
