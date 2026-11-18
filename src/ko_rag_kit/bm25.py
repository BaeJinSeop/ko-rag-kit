"""의존성 없는 BM25 (Okapi)."""

import math
from collections import Counter, defaultdict


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.n = len(docs)
        lengths = [len(d) for d in docs]
        avgdl = sum(lengths) / self.n if self.n else 0
        postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for i, doc in enumerate(docs):
            norm = k1 * (1 - b + b * lengths[i] / avgdl) if avgdl else k1
            for term, tf in Counter(doc).items():
                postings[term].append((i, tf * (k1 + 1) / (tf + norm)))
        self.postings = dict(postings)
        self.idf = {t: math.log(1 + (self.n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def scores(self, query: list[str]) -> list[float]:
        """문서 순서대로 점수를 돌려줍니다. 겹치는 토큰이 없으면 0."""
        out = [0.0] * self.n
        for term in set(query):
            idf = self.idf.get(term, 0.0)
            for i, weight in self.postings.get(term, ()):
                out[i] += idf * weight
        return out
