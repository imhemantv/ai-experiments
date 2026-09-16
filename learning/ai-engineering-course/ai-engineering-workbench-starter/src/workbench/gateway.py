import hashlib
import time
from typing import Protocol

from workbench.contracts import ModelRequest, ModelResult, Usage


class ModelProvider(Protocol):
    def complete(self, request: ModelRequest) -> tuple[str, str, Usage]:
        """Return text, provider request ID, and usage."""


class OfflineProvider:
    """Deterministic provider for tests and zero-cost local experimentation."""

    def complete(self, request: ModelRequest) -> tuple[str, str, Usage]:
        normalized = " ".join(request.prompt.split())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        text = f"Offline response: {normalized}"
        return text, f"offline-{digest}", Usage(
            input_tokens=len(normalized.split()),
            output_tokens=len(text.split()),
        )


class ModelGateway:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    def complete(self, request: ModelRequest) -> ModelResult:
        started = time.perf_counter()
        text, request_id, usage = self._provider.complete(request)
        return ModelResult(
            text=text,
            model=request.model,
            request_id=request_id,
            usage=usage,
            latency_ms=round((time.perf_counter() - started) * 1000),
        )
