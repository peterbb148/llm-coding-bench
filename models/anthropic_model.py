import time
import os
import anthropic
import models.config  # noqa: F401 — loads .env
from models.base import ModelResponse

MODEL_ID = "claude-sonnet-4-6"


def complete(prompt: str, temperature: float = 0) -> ModelResponse:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    chunks = []
    input_tokens = 0
    output_tokens = 0

    start = time.perf_counter()
    with client.messages.stream(
        model=MODEL_ID,
        max_tokens=2048,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)
        usage = stream.get_final_message().usage
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
    elapsed = time.perf_counter() - start

    return ModelResponse(
        model_id=MODEL_ID,
        content="".join(chunks),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        elapsed_seconds=elapsed,
    )
