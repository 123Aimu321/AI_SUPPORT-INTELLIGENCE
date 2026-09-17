from pathlib import Path

import pandas as pd

from sqlalchemy import create_engine, text

from app.core.config import settings


REQUIRED_COLUMNS = {
    "ticket_id",
    "created_at",
    "category",
    "priority",
    "status",
    "response_time_hrs",
    "resolution_time_hrs",
    "agent_id",
    "customer_rating",
    "issue_summary",
}


def load_csv() -> pd.DataFrame:

    csv_path = Path(
        settings.csv_path
    )

    if not csv_path.exists():

        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    df = pd.read_csv(
        csv_path
    )

    df = df.dropna(
        axis=1,
        how="all"
    )

    missing_columns = (
        REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce"
    )

    numeric_columns = [
        "response_time_hrs",
        "resolution_time_hrs",
        "customer_rating",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    string_columns = [
        "ticket_id",
        "category",
        "priority",
        "status",
        "agent_id",
        "issue_summary",
    ]

    for column in string_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    if df["ticket_id"].duplicated().any():

        duplicates = (
            df.loc[
                df["ticket_id"].duplicated(),
                "ticket_id"
            ]
            .tolist()
        )

        raise ValueError(
            f"Duplicate ticket IDs found: "
            f"{duplicates}"
        )

    if df["ticket_id"].isna().any():

        raise ValueError(
            "ticket_id cannot contain null values."
        )

    return df


def initialize_database() -> int:

    df = load_csv()

    database_path = Path(
        settings.database_url.replace(
            "sqlite:///",
            ""
        )
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False
        },
    )

    df.to_sql(
        "support_tickets",
        engine,
        if_exists="replace",
        index=False,
    )

    with engine.connect() as connection:

        count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM support_tickets"
            )
        ).scalar()

    return int(count)