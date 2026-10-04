from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from typing import Any


class EmbeddingUnavailable(RuntimeError):
    """The local embedding model could not produce a vector (Ollama stopped, model missing, ...).

    Search treats this as recoverable and falls back to keyword-only ranking; indexing does not.
    """


class OllamaEmbedder:
    """Local-only embedding client (v0 lab client plus config-driven batching)."""

    def __init__(
        self,
        model: str,
        endpoint: str = "http://127.0.0.1:11434/api/embed",
        timeout_seconds: int = 300,
        keep_alive: str = "30m",
        batch_size: int = 64,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = int(timeout_seconds)
        self.keep_alive = keep_alive
        self.batch_size = max(1, int(batch_size))

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "OllamaEmbedder":
        settings = config["embedding"]
        return cls(
            model=settings["model"],
            endpoint=settings.get("endpoint", "http://127.0.0.1:11434/api/embed"),
            timeout_seconds=settings.get("timeout_seconds", 300),
            keep_alive=settings.get("keep_alive", "30m"),
            batch_size=settings.get("batch_size", 64),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = json.dumps(
            {"model": self.model, "input": texts, "truncate": True, "keep_alive": self.keep_alive}
        ).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            raise EmbeddingUnavailable(
                f"local Ollama embedding request failed for {self.model} at {self.endpoint}: {error}"
            ) from error
        embeddings = result.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingUnavailable(f"unexpected Ollama embedding response: {sorted(result)}")
        return [normalize([float(value) for value in vector]) for vector in embeddings]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


def normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
