from dataclasses import dataclass


@dataclass
class ModelResponse:
    model_id: str
    content: str
    input_tokens: int
    output_tokens: int
    elapsed_seconds: float  # wall-clock from request start to last token

    @property
    def tokens_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.output_tokens / self.elapsed_seconds

    @property
    def chars_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return len(self.content) / self.elapsed_seconds
