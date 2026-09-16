from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    model: str = "offline-demo"
    temperature: float = 0.0


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ModelResult:
    text: str
    model: str
    request_id: str
    usage: Usage
    latency_ms: int
