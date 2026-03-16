from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")

resp = client.responses.create(
    model="grok-4-fast-reasoning",
    input=[
        {"role": "system", "content": "You are Grok 4. Answer in Japanese."},
        {"role": "user", "content": "grok-4で動作確認テストをしてください。"},
    ],
)

print(resp.output_text)
