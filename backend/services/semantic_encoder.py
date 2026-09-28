"""Pinned MiniLM inference on CPU; never downloads files during an API request."""

from functools import lru_cache
import hashlib
import importlib.util
import os
from pathlib import Path
from threading import RLock

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
FILES = {
    "tokenizer.json": {"remote": "tokenizer.json", "sha256": "be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037", "bytes": 466247},
    "model.onnx": {"remote": "onnx/model.onnx", "sha256": "6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452", "bytes": 90405214},
}
_lock = RLock()


class SemanticUnavailable(RuntimeError):
    pass


def model_directory():
    default = Path(__file__).resolve().parents[2] / "data" / "models" / "minilm-l6-v2"
    return Path(os.environ.get("CAREER_SEMANTIC_MODEL_DIR", default)).resolve()


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def model_status():
    dependencies = all(importlib.util.find_spec(name) is not None for name in ("onnxruntime", "tokenizers", "numpy"))
    files_present = all((model_directory() / name).is_file() for name in FILES)
    return {"available": dependencies and files_present, "model_id": MODEL_ID, "revision": MODEL_REVISION,
            "status": "ready_to_load" if dependencies and files_present else "setup_required"}


class MiniLMEncoder:
    def __init__(self, directory):
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
            for name, expected in FILES.items():
                if file_digest(directory / name) != expected["sha256"]:
                    raise SemanticUnavailable("Semantic model files failed verification. Run the model setup script again.")
            self.np = np
            self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
            self.tokenizer.no_truncation()
            self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            options.inter_op_num_threads = 1
            self.session = ort.InferenceSession(str(directory / "model.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
        except SemanticUnavailable:
            raise
        except (ImportError, OSError, RuntimeError, ValueError) as exception:
            raise SemanticUnavailable("Semantic matching is unavailable. Prepare the local model or choose the keyword baseline.") from exception

    def encode(self, texts):
        # The tokenizer has mutable padding configuration; serialize access across requests.
        with _lock:
            vectors = []
            for start in range(0, len(texts), 16):
                encoded = self.tokenizer.encode_batch(texts[start:start + 16])
                if any(len(item.ids) > 256 for item in encoded):
                    raise ValueError("A description fragment exceeds the model's token limit. Shorten that line and try again.")
                inputs = {"input_ids": self.np.array([item.ids for item in encoded], dtype="int64"),
                          "attention_mask": self.np.array([item.attention_mask for item in encoded], dtype="int64"),
                          "token_type_ids": self.np.array([item.type_ids for item in encoded], dtype="int64")}
                names = {item.name for item in self.session.get_inputs()}
                output = self.session.run(None, {key: value for key, value in inputs.items() if key in names})[0]
                mask = inputs["attention_mask"][..., None].astype("float32")
                pooled = (output * mask).sum(axis=1) / self.np.maximum(mask.sum(axis=1), 1e-9)
                pooled /= self.np.maximum(self.np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9)
                vectors.extend(pooled.tolist())
            return vectors


@lru_cache(maxsize=1)
def _load_encoder(directory):
    return MiniLMEncoder(Path(directory))


def get_encoder():
    if not model_status()["available"]:
        raise SemanticUnavailable("Semantic matching is unavailable. Prepare the local model or choose the keyword baseline.")
    with _lock:
        return _load_encoder(str(model_directory()))
