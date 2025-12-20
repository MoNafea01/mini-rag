from pydantic import BaseModel
from typing import Optional

class PushRequest(BaseModel):
    do_reset: Optional[int]=0

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int]=5

class AnswerRequest(BaseModel):
    query: str
    top_k: Optional[int]=5
    temperature: Optional[float]=0.2
    max_tokens: Optional[int]=512
