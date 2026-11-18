"""메모리 하이브리드 인덱스. 벡터(코사인)와 BM25 순위를 RRF로 합칩니다."""

from collections.abc import Sequence

import numpy as np

from .bm25 import BM25


class HybridIndex:
    def __init__(self, chunks: Sequence, vectors, tokens: list[list[str]], rrf_k: int = 60):
        vectors = np.asarray(vectors, dtype=np.float32)
        if not len(chunks) == len(vectors) == len(tokens):
            raise ValueError("chunks, vectors, tokens의 개수가 다릅니다")
        self.chunks = list(chunks)
        self.vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        self.bm25 = BM25(tokens)
        self.rrf_k = rrf_k

    def search(self, query_vector, query_tokens: list[str], top_k: int = 5) -> list[tuple[object, float]]:
        """(청크, RRF 점수)를 점수가 높은 순서로 돌려줍니다."""
        n = len(self.chunks)
        fused = np.zeros(n)
        # 질의 벡터의 크기는 순위에 영향이 없어 정규화하지 않습니다
        by_vector = np.argsort(-(self.vectors @ np.asarray(query_vector, dtype=np.float32)), kind="stable")
        fused[by_vector] += 1 / (self.rrf_k + np.arange(1, n + 1))
        bm = np.asarray(self.bm25.scores(query_tokens))
        by_bm25 = np.argsort(-bm, kind="stable")
        by_bm25 = by_bm25[bm[by_bm25] > 0]  # 겹치는 토큰이 없는 청크는 BM25 순위에 넣지 않습니다
        fused[by_bm25] += 1 / (self.rrf_k + np.arange(1, len(by_bm25) + 1))
        top = np.argsort(-fused, kind="stable")[:top_k]
        return [(self.chunks[i], float(fused[i])) for i in top]
