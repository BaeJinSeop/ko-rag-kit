# 테스트 데이터는 모두 가짜 값입니다. 실제 개인정보를 넣지 마세요.
import pytest

from ko_rag_kit import bm25, chunk, cost, mask, tokenize
from ko_rag_kit.index import HybridIndex


def test_bigram_fallback(monkeypatch):
    monkeypatch.setattr(tokenize, "_kiwi", lambda: None)
    assert tokenize.name() == "bigram"
    assert tokenize.tokenize("예약을 변경 API") == ["예약을", "예약", "약을", "변경", "api"]


def test_kiwi_morphemes():
    pytest.importorskip("kiwipiepy")
    assert tokenize.name() == "kiwi"
    tokens = tokenize.tokenize("예약을 변경하고 싶어요")
    assert "예약" in tokens and "변경" in tokens and "을" not in tokens
    # 형용사(VA), 의존명사(NNB)도 남기고, 영어는 분석 뒤에 소문자로 바꿉니다
    tokens = tokenize.tokenize("API 요금이 비싸요 3번")
    assert {"api", "비싸", "3", "번"} <= set(tokens)


def test_bm25_scores_only_matching_docs():
    scores = bm25.BM25([["예약", "변경"], ["환불", "규정"], []]).scores(["예약"])
    assert scores[0] > 0 and scores[1] == 0 and scores[2] == 0


def test_hybrid_rrf_fusion():
    index = HybridIndex(["a", "b", "c"], [[1, 0], [0, 1], [0.7, 0.7]], tokens=[["x"], ["y"], ["z"]])
    # a는 벡터 1위, c는 벡터 2위 + BM25 1위라서 c가 먼저 나와야 합니다
    assert [c for c, _ in index.search([1, 0], ["z"], top_k=2)] == ["c", "a"]
    with pytest.raises(ValueError):
        HybridIndex(["a"], [[1, 0]], tokens=[])


def test_split_markdown_sections():
    md = "# 안내\n소개\n## 예약\n본문\n```\n## 코드 주석\n```\n### 변경\n변경 방법\n## 빈 섹션\n"
    chunks = chunk.split_markdown(md)
    assert [c.path for c in chunks] == ["안내", "안내 > 예약", "안내 > 예약 > 변경"]
    assert "## 코드 주석" in chunks[1].content
    assert chunks[2].content == "안내 > 예약 > 변경\n\n변경 방법"


def test_split_markdown_meta_frontmatter_comments():
    md = (
        "---\ntitle: 비공개\ntenant: a\n---\n"
        "## 섹션\n본문 <!-- 내부 메모 -->끝\n<!--\n여러 줄\n메모\n-->\n"
        "```html\n<!-- 코드 속 주석 -->\n```\n"
    )
    chunks = chunk.split_markdown(md, title="문서", meta={"tenant": "a"})
    assert len(chunks) == 1 and chunks[0].meta == {"tenant": "a"}
    content = chunks[0].content
    assert "비공개" not in content and "메모" not in content
    assert "본문 끝" in content and "<!-- 코드 속 주석 -->" in content
    assert chunk.split_markdown("본문")[0].meta == {}


def test_long_section_split():
    body = "\n\n".join(["가" * 1000] * 3)
    assert len(chunk.split_markdown(f"## 긴 섹션\n{body}", title="문서")) == 3
    assert [len(p) for p in chunk._split("나" * 4000, 1800)] == [1800, 1800, 400]


def test_mask_keeps_dates():
    masked, found = mask.mask(
        "주민 900101-1234567, 카드 4111 1111 1111 1111, 010-1234-5678로 연락, "
        "사무실 (02) 123-4567, 인터넷전화 070-1234-5678, test@example.com으로 메일, "
        "계좌 110-123-456789, 날짜 2026-11-03"
    )
    assert masked == (
        "주민 [주민번호], 카드 [카드번호], [전화번호]로 연락, "
        "사무실 [전화번호], 인터넷전화 [전화번호], [이메일]으로 메일, "
        "계좌 [계좌번호], 날짜 2026-11-03"
    )
    assert sorted(found) == sorted(["주민번호", "카드번호", "전화번호", "전화번호", "전화번호", "이메일", "계좌번호"])


def test_cost():
    price = cost.Price(input=2, output=10, cache_read=0.2, cache_write=2.5)
    assert cost.cost(price, 1_000_000, 100_000, cache_read_tokens=1_000_000) == pytest.approx(3.2)
