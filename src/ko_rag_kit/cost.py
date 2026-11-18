"""토큰 수와 단가(USD/100만 토큰)로 요청 비용을 계산합니다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    """USD/100만 토큰. 단가는 자주 바뀌므로 제공사 가격표를 보고 직접 채우세요."""

    input: float
    output: float
    cache_read: float = 0.0
    cache_write: float = 0.0


def cost(
    price: Price,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """USD. input_tokens에는 캐시로 읽거나 쓴 토큰을 빼고 넣으세요. 제공사마다 사용량 집계 방식이 다릅니다."""
    return (
        input_tokens * price.input
        + output_tokens * price.output
        + cache_read_tokens * price.cache_read
        + cache_write_tokens * price.cache_write
    ) / 1_000_000
