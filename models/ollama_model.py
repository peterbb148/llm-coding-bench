import os
import httpx
from models.base import ModelResponse

MODEL_ID = "glm-4.7-flash:latest"


def complete(prompt: str, temperature: float = 0) -> ModelResponse:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    response = httpx.post(
        f"{host}/api/generate",
        json={
            "model": MODEL_ID,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()

    # Ollama provides native token counts and duration — no wall-clock needed
    output_tokens = data["eval_count"]
    elapsed = data["eval_duration"] / 1e9  # nanoseconds → seconds

    return ModelResponse(
        model_id=MODEL_ID,
        content=data["response"],
        input_tokens=data.get("prompt_eval_count", 0),
        output_tokens=output_tokens,
        elapsed_seconds=elapsed,
    )
