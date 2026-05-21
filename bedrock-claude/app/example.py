from anthropic import AnthropicBedrock, AsyncAnthropicBedrock

model_id = "anthropic.claude-3-haiku-20240307-v1:0"
user_message = "Hello Claude! Can you do zero-shot classification?"
sync_client = AnthropicBedrock()
async_client = AsyncAnthropicBedrock()
ASYNC = 0
if ASYNC == 1:
    message = await async_client.messages.create(
        model=model_id,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
else:
    message = sync_client.messages.create(
        model=model_id,
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}]
    )
print(message.content[0].text)
