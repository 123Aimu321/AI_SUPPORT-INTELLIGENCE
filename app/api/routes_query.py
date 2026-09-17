from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    QueryRequest,
    QueryResponse,
)

from app.services.query_service import (
    QueryService,
)


router = APIRouter()

query_service = QueryService()


@router.post(
    "/query",
    response_model=QueryResponse
)
def query_support_data(
    request: QueryRequest
):

    try:

        result = query_service.answer_question(
            request.question
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc