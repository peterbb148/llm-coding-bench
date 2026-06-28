import time
import os
import openai
from models.base import ModelResponse

MODEL_ID = "gpt-5"


def complete(prompt: str, temperature: float = 0) -> ModelResponse:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    chunks = []
    input_tokens = 0
    output_tokens = 0

    start = time.perf_counter()
    with client.chat.completions.create(
        model=MODEL_ID,
        temperature=temperature,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True},
    ) as stream:
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
    elapsed = time.perf_counter() - start

    return ModelResponse(
        model_id=MODEL_ID,
        content="".join(chunks),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        elapsed_seconds=elapsed,
    )
