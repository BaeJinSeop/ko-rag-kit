"""마크다운을 ## 섹션, ### 소제목 단위로 나눕니다."""

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"(#{1,3}) +(.*\S)")
_FRONTMATTER = re.compile(r"\A---[ \t]*\n(?:.*?\n)?---[ \t]*(?:\n|\Z)", re.S)
_CODE_BLOCK = re.compile(r"(^[ \t]*(?:```|~~~).*?^[ \t]*(?:```|~~~)[^\n]*$)", re.M | re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)


@dataclass
class Chunk:
    content: str  # "문서 > 섹션 > 소제목" 경로 + 본문. 임베딩과 BM25에는 이 값을 씁니다.
    path: str
    meta: dict = field(default_factory=dict)  # 검색 필터(where)에 씁니다. 예: {"tenant": "a"}


def split_markdown(text: str, title: str = "", max_chars: int = 1800, meta: dict | None = None) -> list[Chunk]:
    """title이 없으면 첫 # 제목을 문서 이름으로 씁니다. meta는 이 문서의 모든 청크에 붙습니다.

    맨 앞 frontmatter(--- … ---)는 해석하지 않고 잘라냅니다. 필요하면 직접 읽어 meta로 넘기세요.
    코드 블록 밖의 HTML 주석은 지웁니다. 내부 메모가 답변으로 새지 않게 하기 위해서입니다.
    """
    text = _FRONTMATTER.sub("", text)
    parts = _CODE_BLOCK.split(text)  # 홀수 번째 조각이 코드 블록입니다
    text = "".join(p if i % 2 else _COMMENT.sub("", p) for i, p in enumerate(parts))

    sections: list[tuple[str, str, list[str]]] = [("", "", [])]
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
        elif not in_code and (m := _HEADING.match(line)):
            level, heading = len(m[1]), m[2]
            if level == 1:
                title = title or heading
            elif level == 2:
                sections.append((heading, "", []))
            else:
                sections.append((sections[-1][0], heading, []))
            continue
        sections[-1][2].append(line)

    chunks = []
    for h2, h3, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        path = " > ".join(p for p in (title, h2, h3) if p)
        chunks += [
            Chunk(f"{path}\n\n{part}" if path else part, path, dict(meta or {})) for part in _split(body, max_chars)
        ]
    return chunks


def _split(body: str, max_chars: int) -> list[str]:
    """문단을 max_chars 안에서 묶습니다. 문단 하나가 더 길면 글자 수로 자릅니다."""
    if len(body) <= max_chars:
        return [body]
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", body):
        for piece in (para[i : i + max_chars] for i in range(0, len(para), max_chars)):
            if current and len(current) + 2 + len(piece) > max_chars:
                parts.append(current)
                current = piece
            else:
                current = f"{current}\n\n{piece}" if current else piece
    return parts + [current] if current else parts
