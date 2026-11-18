"""한국어 토크나이저. kiwipiepy가 있으면 형태소, 없으면 단어 + 한글 2글자 묶음(bigram)."""

import re
from functools import cache

# 일반·고유명사, 동사, 어근, 외국어, 숫자
_KIWI_TAGS = {"NNG", "NNP", "VV", "XR", "SL", "SN"}
_WORD = re.compile(r"[가-힣]+|[a-z0-9]+")


@cache
def _kiwi():
    try:
        from kiwipiepy import Kiwi
    except ImportError:
        return None
    return Kiwi()


def name() -> str:
    """인덱스와 함께 저장해 두세요. 적재와 검색의 토크나이저가 다르면 BM25가 맞지 않습니다."""
    return "kiwi" if _kiwi() else "bigram"


def tokenize(text: str) -> list[str]:
    text = text.lower()
    if kiwi := _kiwi():
        # 동사는 VV-R/VV-I처럼 활용 표시가 붙어 나올 수 있어 앞부분만 봅니다
        return [t.form for t in kiwi.tokenize(text) if t.tag.split("-")[0] in _KIWI_TAGS]
    tokens = []
    for word in _WORD.findall(text):
        tokens.append(word)
        if len(word) > 2 and "가" <= word[0] <= "힣":
            tokens += [word[i : i + 2] for i in range(len(word) - 1)]
    return tokens
