from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import AnomalyResponse
from app.services.anomaly_service import AnomalyService


router = APIRouter()

anomaly_service = AnomalyService()


@router.get(
    "/anomalies",
    response_model=AnomalyResponse,
)
def get_anomalies(
    period: str | None = Query(
        default=None,
        description="Optional period: this_week or this_month",
    ),
):
    try:

        if period not in {
            None,
            "this_week",
            "this_month",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid period. "
                    "Use this_week or this_month."
                ),
            )

        result = anomaly_service.detect_anomalies(
            period=period
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc