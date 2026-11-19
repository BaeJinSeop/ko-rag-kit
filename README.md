# ko-rag-kit

한국어 문서를 대상으로 하는 RAG용 작은 도구 모음입니다. BM25와 벡터 검색을 섞는 하이브리드 검색, 한국어 형태소 토크나이저, 마크다운 청크 분할, 개인정보 마스킹, LLM 비용 계산을 담습니다.

> **상태: 0.1.0 (PyPI 공개 전).** 아래 모듈이 모두 들어 있습니다. 저장소를 받아 `pip install -e .`로 설치합니다.

## 왜 만드나

- 영어 기준 토크나이저로 한국어 BM25를 돌리면 조사·어미 때문에 같은 단어끼리 잘 맞지 않습니다. 형태소 분석으로 이 문제를 줄입니다.
- 청크가 수만 개 이하라면 벡터 DB 없이 메모리에서 numpy로 계산해도 수 ms 안에 끝납니다. 이 규모에서는 무거운 프레임워크 없이 필요한 부분만 쓰는 쪽이 낫습니다.

## 구성

| 모듈 | 하는 일 |
|---|---|
| `tokenize` | 한국어 토크나이저. [kiwipiepy](https://github.com/bab2min/kiwipiepy)가 있으면 명사·수사·동사·형용사·어근·외국어·숫자·한자 형태소를 쓰고, 없으면 단어 + 한글 2글자 묶음(bigram)으로 대신합니다. |
| `bm25` | 의존성 없는 BM25 (`k1=1.4`, `b=0.75`) |
| `index` | 메모리 하이브리드 인덱스. 벡터(코사인)와 BM25 순위를 RRF(`k=60`)로 합칩니다. |
| `chunk` | 마크다운을 `##` 섹션 단위로 나누고, `###` 소제목이 있으면 더 나눕니다. 1800자보다 긴 섹션은 문단 단위로 자릅니다. 청크 앞에 "문서 > 섹션 > 소제목" 경로를 붙입니다. |
| `mask` | 주민번호·카드번호·휴대전화·지역번호·070 전화·이메일·계좌번호를 `[전화번호]`처럼 가립니다. 날짜(`2026-11-03`)는 건드리지 않습니다. |
| `embed` | 임베딩. 기본은 로컬 [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)이고, `provider="voyage"`로 Voyage API를 쓸 수 있습니다. API 키는 `VOYAGE_API_KEY` 환경변수로만 받습니다. |
| `cost` | 입력·출력·캐시 토큰 수와 단가(`Price`, USD/100만 토큰)로 요청 비용을 계산합니다. 단가는 자주 바뀌어 기본값을 넣지 않았습니다. |

## 설치 (공개 후)

```bash
pip install ko-rag-kit                # 핵심 (numpy만 필요)
pip install "ko-rag-kit[korean]"      # + kiwipiepy 형태소 분석
pip install "ko-rag-kit[embed]"       # + 로컬 bge-m3 임베딩 (sentence-transformers)
```

Python 3.12 이상.

## 사용 예

```python
from ko_rag_kit import chunk, embed, mask, tokenize
from ko_rag_kit.index import HybridIndex

chunks = chunk.split_markdown(open("guide.md").read(), title="사용 안내")
vecs = embed.embed([c.content for c in chunks], "document")
index = HybridIndex(chunks, vecs, tokens=[tokenize.tokenize(c.content) for c in chunks])

question, _ = mask.mask("010-1234-5678로 예약 변경은 어떻게 하나요?")
hits = index.search(embed.embed([question], "query")[0], tokenize.tokenize(question), top_k=5)
for c, score in hits:  # (청크, RRF 점수), 점수 높은 순
    print(c.path, score)
```

`mask.mask()`는 `(가린 문장, 가린 종류 목록)`을 돌려줍니다. 예: `("[전화번호]로 예약 변경은 어떻게 하나요?", ["전화번호"])`

## 개발

```bash
uv run pytest                    # 형태소 분석기 없이 (bigram)
uv run --with kiwipiepy pytest   # kiwi 경로까지
```

테스트 데이터는 모두 가짜 값입니다. 실제 개인정보나 API 키는 저장소에 넣지 마세요. `.env`와 `data/`는 `.gitignore`에 들어 있습니다.

## 설계 메모

- **적재와 검색은 같은 토크나이저를 써야 합니다.** kiwi와 bigram은 토큰이 다르므로, 인덱스를 만들 때 쓴 토크나이저 이름(`tokenize.name()`)을 함께 저장해 두세요.
- **임베딩 모델을 바꾸면 전체를 다시 임베딩해야 합니다.** 모델마다 차원과 벡터 공간이 다릅니다.
- **마스킹은 형식이 있는 값만 잡습니다.** 이름·주소처럼 형식이 없는 값은 정규식으로 잡을 수 없으니, 입력 화면에도 개인정보를 넣지 말라는 안내를 함께 두세요.

## 라이선스

미정
