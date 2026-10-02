from typing import List
from pydantic import BaseModel, Field


class Finding(BaseModel):
    title: str
    severity: str  # High / Medium / Low
    explanation: str
    sources: List[str] = Field(default_factory=list)


class Report(BaseModel):
    company: str
    executive_summary: str
    risks: List[Finding] = Field(default_factory=list)
    growth_opportunities: List[Finding] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    sources: List[str]