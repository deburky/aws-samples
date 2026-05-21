# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "boto3==1.38.24",
#     "litellm==1.71.1",
#     "marimo",
# ]
# ///

import marimo

__generated_with = "0.13.13"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Text2SQL — Ask your database in plain English

    Type a question about your data. Claude generates the SQL, executes it
    against Redshift via the Data API, and returns the results.
    """
    )
    return


# ---------------------------------------------------------------------------
# AWS credential check
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    import os
    import boto3

    def check_aws_config():
        has_creds = False
        profile = os.environ.get("AWS_PROFILE", "")
        try:
            session = boto3.Session(
                profile_name=profile if profile else None
            )
            credentials = session.get_credentials()
            if credentials:
                has_creds = True
        except Exception:
            pass
        return {"has_credentials": has_creds}

    aws_config = check_aws_config()
    return (aws_config,)


@app.cell(hide_code=True)
def _(aws_config, mo):
    mo.stop(
        not aws_config["has_credentials"],
        mo.md("""
### AWS Credentials Not Found

Configure credentials via one of:
1. `export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...`
2. `aws configure`
3. Set `AWS_PROFILE` to a profile in `~/.aws/credentials`
        """),
    )
    return


# ---------------------------------------------------------------------------
# Load schema context (for the LLM system prompt)
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    from pathlib import Path

    _schema_path = Path(__file__).parent / "schema" / "schema_context.md"
    if _schema_path.exists():
        schema_context = _schema_path.read_text()
    else:
        schema_context = "No schema context file found. Ask the user to describe the tables."
    return (schema_context,)


# ---------------------------------------------------------------------------
# Configuration form
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _(mo):
    import os as _os

    model_options = [
        "bedrock/converse/us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "bedrock/converse/us.anthropic.claude-sonnet-4-6",
        "bedrock/converse/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    ]

    region_options = [
        "eu-west-1",
        "us-east-1",
        "us-west-2",
        "eu-central-1",
    ]

    model = mo.ui.dropdown(
        options=model_options, value=model_options[0], label="Bedrock Model"
    )
    region = mo.ui.dropdown(
        options=region_options,
        value=_os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"),
        label="AWS Region",
    )
    profile = mo.ui.text(
        value=_os.environ.get("AWS_PROFILE", ""),
        label="AWS Profile (optional)",
        placeholder="Leave empty for default credentials",
    )
    max_rows = mo.ui.slider(10, 500, value=50, step=10, label="Max rows to display")

    config_form = (
        mo.md("""
**Configuration**
{model}
{region}
{profile}
{max_rows}
        """)
        .batch(
            model=model,
            region=region,
            profile=profile,
            max_rows=max_rows,
        )
        .form(submit_button_label="Apply")
    )

    config_form
    return (config_form,)


# ---------------------------------------------------------------------------
# Text2SQL chat model — custom handler that generates SQL, runs it, formats
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _(config_form, mo, schema_context):
    import json
    import traceback
    from litellm import completion

    def _build_system_prompt(schema: str) -> str:
        return f"""You are a SQL assistant. The user will ask questions about data.
Your job is to write a read-only SQL query that answers their question.

RULES:
- Output ONLY a JSON object: {{"sql": "<your query>", "explanation": "<one-line explanation>"}}
- SELECT queries only. Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Use standard SQL compatible with Amazon Redshift.
- If the question is ambiguous, make a reasonable assumption and state it in the explanation.
- Limit results to 200 rows unless the user asks for more.

DATABASE SCHEMA:
{schema}"""

    def text2sql_handler(messages, config):
        """Chat handler: take user question, generate SQL, execute, return results."""
        if config_form.value is None:
            return "Please submit the configuration form first."

        cfg = config_form.value
        bedrock_model = cfg["model"]
        bedrock_region = cfg["region"]
        bedrock_profile = cfg["profile"]
        row_limit = cfg["max_rows"]

        # Build messages for the LLM
        system_prompt = _build_system_prompt(schema_context)
        llm_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            llm_messages.append({"role": m.role, "content": m.content})

        # Call Bedrock via litellm
        import os
        os.environ["LITELLM_DROP_PARAMS"] = "True"
        kwargs = {
            "model": bedrock_model,
            "messages": llm_messages,
            "max_tokens": 1024,
            "temperature": 0,
            "aws_region_name": bedrock_region,
        }
        if bedrock_profile.strip():
            kwargs["aws_profile_name"] = bedrock_profile.strip()

        try:
            resp = completion(**kwargs)
            raw = resp.choices[0].message.content.strip()
        except Exception as e:
            return f"**Bedrock error:** {e}"

        # Parse the JSON response
        try:
            # Handle markdown code blocks
            cleaned = raw
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
            sql = parsed["sql"]
            explanation = parsed.get("explanation", "")
        except (json.JSONDecodeError, KeyError):
            return f"**Could not parse model response as JSON.**\n\nRaw output:\n```\n{raw}\n```"

        # Safety check — reject non-SELECT
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return f"**Blocked:** Only SELECT / WITH queries are allowed.\n\nGenerated SQL:\n```sql\n{sql}\n```"

        # Execute the query via Redshift Data API
        try:
            from db import execute_query
            columns, rows = execute_query(sql)
        except Exception as e:
            return (
                f"**Query failed:** `{e}`\n\n"
                f"**SQL:**\n```sql\n{sql}\n```\n\n"
                f"**Explanation:** {explanation}"
            )

        # Format results
        if not columns:
            return f"Query executed successfully (no result set).\n\n```sql\n{sql}\n```"

        display_rows = rows[:row_limit]
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        body = "\n".join(
            "| " + " | ".join(str(v) if v is not None else "" for v in row) + " |"
            for row in display_rows
        )
        truncation = ""
        if len(rows) > row_limit:
            truncation = f"\n\n*Showing {row_limit} of {len(rows)} rows.*"

        return (
            f"**{explanation}**\n\n"
            f"```sql\n{sql}\n```\n\n"
            f"{header}\n{separator}\n{body}{truncation}"
        )

    # Render the chat widget
    mo.stop(
        config_form.value is None,
        mo.md("Submit the configuration above to start."),
    )

    chatbot = mo.ui.chat(
        text2sql_handler,
        prompts=[
            "How many customers do we have by country?",
            "What are the top 5 products by revenue?",
            "Show me monthly order totals for 2024",
            "Which customers have never placed an order?",
        ],
        max_height=600,
    )
    chatbot
    return


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
---

**Architecture:** User question → Claude (Bedrock) generates SQL →
SQL executed against Redshift (Data API) → results displayed.

All Bedrock calls logged in CloudTrail. Redshift access is read-only, scoped to the configured DbUser.
    """
    )
    return


if __name__ == "__main__":
    app.run()
