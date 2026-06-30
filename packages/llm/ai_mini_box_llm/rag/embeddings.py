from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

ONNX_MODEL_URL = "https://huggingface.co/optimum/all-MiniLM-L6-v2/resolve/main/model.onnx"
LOCAL_PATH = "data/embeddings/model.onnx"


class EmbeddingModel:
    def __init__(self):
        self._session: Any = None
        self._input_name: str | None = None
        self._output_name: str | None = None
        self._load()

    def _load(self) -> None:
        path = Path(LOCAL_PATH)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                logger.info("Downloading ONNX model from {}", ONNX_MODEL_URL)
                urllib.request.urlretrieve(ONNX_MODEL_URL, str(path))
                logger.info("ONNX model downloaded to {}", path)
            except Exception as e:
                logger.warning("Failed to download ONNX model: {}. RAG disabled.", e)
                return
        try:
            import onnxruntime
            self._session = onnxruntime.InferenceSession(str(path))
            self._input_names = [inp.name for inp in self._session.get_inputs()]
            self._output_name = self._session.get_outputs()[0].name
            logger.info("ONNX embedding model loaded (384 dim). Inputs: {}", self._input_names)
        except Exception as e:
            logger.warning("Failed to load ONNX model: {}. RAG disabled.", e)

    @property
    def available(self) -> bool:
        return self._session is not None

    def embed(self, text: str) -> list[float]:
        if not self._session or not text.strip():
            return []
        input_ids = self._tokenize(text)
        feed = {"input_ids": input_ids}
        if "attention_mask" in self._input_names:
            feed["attention_mask"] = np.where(input_ids != 0, 1, 0).astype(np.int64)
        if "token_type_ids" in self._input_names:
            feed["token_type_ids"] = np.zeros_like(input_ids)
        result = self._session.run([self._output_name], feed)[0]
        vec = result[0] / np.linalg.norm(result[0])
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self._session or not texts:
            return []
        results = []
        for t in texts:
            results.append(self.embed(t))
        return results

    def _tokenize(self, text: str) -> np.ndarray:
        import numpy as np
        arr = np.zeros((1, 128), dtype=np.int64)
        tokens = [101]
        for ch in text.lower()[:126]:
            tokens.append(ord(ch))
        tokens.append(102)
        tokens = tokens[:128]
        arr[0, :len(tokens)] = tokens
        return arr
