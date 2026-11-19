"""임베딩. 기본은 로컬 BAAI/bge-m3, provider="voyage"면 Voyage API를 씁니다."""

import json
import os
import urllib.request
from functools import cache
from typing import Literal

import numpy as np

_VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
_VOYAGE_BATCH = 128


@cache
def _local_model(model: str):
    from sentence_transformers import SentenceTransformer  # pip install "ko-rag-kit[embed]"

    return SentenceTransformer(model)


def embed(
    texts: list[str],
    kind: Literal["document", "query"],
    provider: Literal["local", "voyage"] = "local",
    model: str | None = None,
) -> np.ndarray:
    """(len(texts), 차원) float32 배열. 모델을 바꾸면 기존 청크도 모두 다시 임베딩해야 합니다."""
    if provider == "voyage":
        return _voyage(texts, kind, model or "voyage-4")
    # bge-m3는 질의와 문서에 별도 접두어가 필요 없어 kind를 쓰지 않습니다
    vectors = _local_model(model or "BAAI/bge-m3").encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def _voyage(texts: list[str], kind: str, model: str) -> np.ndarray:
    key = os.environ.get("VOYAGE_API_KEY")
    if not key:
        raise RuntimeError("VOYAGE_API_KEY 환경변수를 설정하세요. 키를 코드나 저장소에 넣지 마세요.")
    out = []
    for i in range(0, len(texts), _VOYAGE_BATCH):
        request = urllib.request.Request(
            _VOYAGE_URL,
            data=json.dumps({"input": texts[i : i + _VOYAGE_BATCH], "model": model, "input_type": kind}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)["data"]
        out += [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]
    return np.asarray(out, dtype=np.float32)
