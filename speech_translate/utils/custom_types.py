from dataclasses import dataclass
from typing import Optional, TypedDict, List


class ToInsert(TypedDict):
    text: str
    color: Optional[str]
    is_last: Optional[bool]


class StableTsWordResult(TypedDict):
    word: str
    start: float
    end: float
    probability: float
    tokens: List[int]
    segment_id: int
    id: int


class OriWordResult(TypedDict):
    word: str
    start: float
    end: float
    probability: float


class StableTsSegmentResult(TypedDict):
    start: float
    end: float
    text: str
    seek: int
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List[StableTsWordResult]
    id: int


class OriSegmentResult(TypedDict):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List[OriWordResult]


@dataclass
class StableTsResultDict(TypedDict):
    text: str
    segments: List[StableTsSegmentResult]
    language: str
    time_scale: Optional[float]
    ori_dict: OriSegmentResult
