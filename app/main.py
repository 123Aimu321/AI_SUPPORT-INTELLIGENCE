from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_health import (
    router as health_router
)

from app.api.routes_query import (
    router as query_router
)

from app.api.routes_anomaly import (
    router as anomaly_router
)

from app.services.ingestion import (
    initialize_database
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print(
        "Initializing database..."
    )

    try:

        count = initialize_database()

        print(
            f"Loaded {count} support tickets."
        )

    except Exception as exc:

        print(
            "Database initialization failed: "
            f"{exc}"
        )

    yield


app = FastAPI(
    title="AI Support Intelligence",
    version="1.0.0",
    description=(
        "AI-powered customer support "
        "analytics and anomaly detection system."
    ),
    lifespan=lifespan,
)


app.include_router(
    health_router
)

app.include_router(
    query_router
)

app.include_router(
    anomaly_router
)