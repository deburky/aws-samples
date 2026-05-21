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
    # AWS Bedrock Chat

    This example demonstrates using AWS Bedrock with marimo's chat interface.

    AWS Bedrock provides access to foundation models from leading AI companies like Anthropic, Meta, and others.
    """
    )
    return

@app.cell(hide_code=True)
def _():
    import os
    import boto3

    def check_aws_config():
        """Check if AWS configuration is available"""
        # Check for credentials
        has_creds = False
        try:
            session = boto3.Session(profile_name="Sagemaker")  # <-- fixed here
            credentials = session.get_credentials()
            if credentials:
                has_creds = True
        except Exception as e:
            print(f"Error loading profile: {e}")
            pass

        return {"has_credentials": has_creds}

    # Run the check
    aws_config = check_aws_config()

    os.environ["LITELLM_DROP_PARAMS"] = "True"
    return (aws_config,)

@app.cell(hide_code=True)
def _(aws_config, mo):
    # Display AWS configuration status
    mo.stop(
        not aws_config["has_credentials"],
        mo.md("""
            ### ⚠️ AWS Credentials Not Found

            To use AWS Bedrock, you need AWS credentials configured.
            Options:
            1. Set environment variables:
            ```
            export AWS_ACCESS_KEY_ID=your_key
            export AWS_SECRET_ACCESS_KEY=your_secret
            ```

            2. Configure AWS CLI:
            ```
            aws configure
            ```

            3. Use an AWS profile in ~/.aws/credentials
        """),
    )
    return

@app.cell(hide_code=True)
def _(mo):
    # UI for model configuration

    # Predefined model options
    model_options = [
        "bedrock/converse/us.writer.palmyra-x4-v1:0",
        "bedrock/converse/us.writer.palmyra-x5-v1:0",
        "bedrock/converse/us.anthropic.claude-sonnet-4-20250514-v1:0",
        "bedrock/converse/us.anthropic.claude-opus-4-20250514-v1:0",
        "bedrock/converse/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "bedrock/converse/us.deepseek.r1-v1:0",
        "Custom",
    ]

    # Region options
    region_options = [
        "us-east-1",
        "us-west-2",
        "eu-central-1",
        "ap-northeast-1",
        "ap-southeast-1",
    ]

    # Model selection
    model = mo.ui.dropdown(
        options=model_options, value=model_options[0], label="AWS Bedrock Model"
    )

    # Region selection
    region = mo.ui.dropdown(options=region_options, value="us-west-2", label="AWS Region")

    # Optional profile name
    profile = mo.ui.text(
        value="",
        label="AWS Profile (optional)",
        placeholder="Leave empty to use default credentials",
    )

    # System message
    system_message = mo.ui.text_area(
        value="You are a helpful, harmless assistant. Provide clear, concise answers.",
        label="System Message",
        rows=2,
    )

    # Create a form to wrap all inputs
    config_form = (
        mo.md("""
            AWS Bedrock Chat Configuration:
            {model}
            {region}
            {profile}
            {system_message}
        """)
        .batch(
            model=model,
            region=region,
            profile=profile,
            system_message=system_message,
        )
        .form(
            submit_button_label="Update Chat Configuration",
        )
    )

    temperature = mo.ui.slider(0.1, 1.0, value=1, step=0.1, label="Temperature")
    max_tokens = mo.ui.slider(5, 1_000_000, value=2048, step=100, label="Max tokens")
    mo.vstack([config_form, mo.md("### LLM parameters"), temperature, max_tokens])
    return config_form, max_tokens, temperature

@app.cell(hide_code=True)
def _(config_form, max_tokens, mo, temperature):
    # Define the chat creation function
    def create_chat(config_form):
        if config_form.value is None:
            return mo.md("➡️ Please submit the form above to start the chat.")

        model = config_form.value["model"]
        region = config_form.value["region"]
        system_message = config_form.value["system_message"]
        profile = config_form.value["profile"]

        try:
            # Set only supported params for the chosen model
            params = dict(
                temperature=temperature.value,
                max_tokens=max_tokens.value,
                top_k=1,
                top_p=1.0,
                frequency_penalty=0,
                presence_penalty=0,
            )
            chat_config = mo.ai.ChatModelConfig(**params)

            model_kwargs = {
                "model": model,
                "region_name": region,
                "system_message": system_message,
            }
            if profile.strip():
                model_kwargs["profile_name"] = profile.strip()

            chatbot = mo.ui.chat(
                mo.ai.llm.bedrock(**model_kwargs),
                allow_attachments=[
                    "image/png",
                    "image/jpeg",
                    "application/pdf",
                    "text/plain",
                    "text/markdown",
                    "text/csv",
                    # DOCX is allowed in the UI, but will likely not be processed by the model,
                    # so you may want to leave it out or handle it in your app logic:
                    # "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ],
                prompts=[
                    "Hello",
                    "How are you?",
                    "I'm doing great, how about you?",
                ],
                max_height=400,
                config=chat_config,
            )
            return chatbot
        except Exception as e:
            return mo.md(f"**Error initializing chat**: {str(e)}")

    # Display the chat interface (always put the widget last)
    create_chat(config_form)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Notes on AWS Bedrock Usage

    1. **Model Access**: You need to request access to the specific models you want to use in the AWS Bedrock console.

    2. **Pricing**: Using AWS Bedrock incurs usage costs based on the number of input and output tokens. Check the [AWS Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) for details.

    3. **Regions**: AWS Bedrock is not available in all AWS regions. Make sure to choose a region where Bedrock is available.

    4. **Authentication**: This example uses the standard AWS credential chain (environment variables, AWS config files, or instance profiles). You can also provide explicit credentials when creating the model.

    5. **Troubleshooting**: If you encounter issues, check:
    - That your AWS credentials are configured correctly
    - That you have requested model access in the AWS Bedrock console
    - That you're using a region where the selected model is available
    """
    )
    return

if __name__ == "__main__":
    app.run()