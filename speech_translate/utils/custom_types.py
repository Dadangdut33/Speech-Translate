from typing import Optional, TypedDict, List


class ToInsert(TypedDict):
    text: str
    color: Optional[str]
    is_last: Optional[bool]


class WhisperWordResult(TypedDict):
    text: str
    start: float
    end: float
    confidence: float


class WhisperSegmentResult(TypedDict):
    id: int
    seek: float
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    confidence: float
    words: List[WhisperWordResult]


class WhisperResult(TypedDict):
    text: str
    segments: List[WhisperSegmentResult]
    language: str
