"""형식이 있는 개인정보를 [전화번호]처럼 가립니다. 이름·주소처럼 형식이 없는 값은 잡지 못합니다."""

import re


def _digits(s: str) -> int:
    return sum(c.isdigit() for c in s)


# 순서가 중요합니다: 앞 규칙이 먼저 가린 값은 뒤 규칙(특히 계좌번호)에 걸리지 않습니다.
_RULES = [
    ("이메일", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"), None),
    ("주민번호", re.compile(r"(?<!\d)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])-?[1-8]\d{6}(?!\d)"), None),
    ("카드번호", re.compile(r"(?<!\d)\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}(?!\d)"), None),
    ("전화번호", re.compile(r"(?<!\d)01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"), None),
    ("전화번호", re.compile(r"(?<!\d)\(?0(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4])\)?[-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"), None),
    # 은행마다 자리 배치가 달라 하이픈으로 나뉜 10~14자리 숫자를 계좌로 봅니다. 날짜(8자리)는 제외됩니다.
    ("계좌번호", re.compile(r"(?<![\d-])\d{2,6}(?:-\d{2,7}){2,3}(?![\d-])"), lambda s: 10 <= _digits(s) <= 14),
]


def mask(text: str) -> tuple[str, list[str]]:
    """(가린 문장, 가린 종류 목록)을 돌려줍니다."""
    found: list[str] = []
    for label, pattern, check in _RULES:

        def replace(m: re.Match, label=label, check=check) -> str:
            if check and not check(m[0]):
                return m[0]
            found.append(label)
            return f"[{label}]"

        text = pattern.sub(replace, text)
    return text, found
