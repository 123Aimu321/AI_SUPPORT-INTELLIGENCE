from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
    )


class QueryResponse(BaseModel):

    question: str

    answer: str

    data: list[
        dict[str, Any]
    ]

    intent: dict[str, Any]


class AnomalyResponse(BaseModel):

    total_anomalies: int

    anomalies: list[
        dict[str, Any]
    ]