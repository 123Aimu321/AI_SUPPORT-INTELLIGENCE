from typing import Any

import pandas as pd
from sqlalchemy import create_engine

from app.core.config import settings


class AnomalyService:

    def __init__(self):

        self.engine = create_engine(
            settings.database_url,
            connect_args={
                "check_same_thread": False
            },
        )

    def detect_anomalies(
        self,
        period: str | None = None,
    ) -> dict[str, Any]:

        df = pd.read_sql(
            "SELECT * FROM support_tickets",
            self.engine,
        )

        if df.empty:

            return {
                "total_anomalies": 0,
                "anomalies": [],
            }

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce",
        )

        df["response_time_hrs"] = pd.to_numeric(
            df["response_time_hrs"],
            errors="coerce",
        )

        df["resolution_time_hrs"] = pd.to_numeric(
            df["resolution_time_hrs"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # OPTIONAL TIME FILTER
        # ----------------------------------------------------

        if period:

            start_date, end_date = (
                self._get_time_range(period)
            )

            start_timestamp = pd.Timestamp(
                start_date
            )

            end_timestamp = pd.Timestamp(
                end_date
            )

            df = df[
                (df["created_at"] >= start_timestamp)
                & (df["created_at"] < end_timestamp)
            ].copy()

        if df.empty:

            return {
                "total_anomalies": 0,
                "anomalies": [],
            }

        anomalies = []

        # ----------------------------------------------------
        # CRITICAL UNRESOLVED > 24 HOURS
        # ----------------------------------------------------

        critical_mask = (
            (df["priority"] == "Critical")
            & (df["status"] != "Resolved")
            & (df["resolution_time_hrs"] > 24)
        )

        for _, row in df.loc[
            critical_mask
        ].iterrows():

            anomalies.append(
                self._create_anomaly(
                    row=row,
                    anomaly_type=(
                        "Critical unresolved ticket"
                    ),
                    severity="Critical",
                    reason=(
                        "Critical priority ticket "
                        "is unresolved and has "
                        "exceeded 24 hours."
                    ),
                )
            )

        # ----------------------------------------------------
        # HIGH UNRESOLVED > 24 HOURS
        # ----------------------------------------------------

        high_mask = (
            (df["priority"] == "High")
            & (df["status"] != "Resolved")
            & (df["resolution_time_hrs"] > 24)
        )

        for _, row in df.loc[
            high_mask
        ].iterrows():

            anomalies.append(
                self._create_anomaly(
                    row=row,
                    anomaly_type=(
                        "High priority unresolved ticket"
                    ),
                    severity="High",
                    reason=(
                        "High priority ticket "
                        "is unresolved and has "
                        "exceeded 24 hours."
                    ),
                )
            )

        # ----------------------------------------------------
        # UNRESOLVED > 48 HOURS
        # ----------------------------------------------------

        long_unresolved_mask = (
            (df["status"] != "Resolved")
            & (df["resolution_time_hrs"] > 48)
        )

        for _, row in df.loc[
            long_unresolved_mask
        ].iterrows():

            if (
                row["priority"] == "Critical"
                and row["resolution_time_hrs"] > 24
            ):
                continue

            if (
                row["priority"] == "High"
                and row["resolution_time_hrs"] > 24
            ):
                continue

            anomalies.append(
                self._create_anomaly(
                    row=row,
                    anomaly_type=(
                        "Long unresolved ticket"
                    ),
                    severity=(
                        "High"
                        if row["priority"] == "Medium"
                        else "Medium"
                    ),
                    reason=(
                        "The ticket remains unresolved "
                        "and its resolution time has "
                        "exceeded 48 hours."
                    ),
                )
            )

        # ----------------------------------------------------
        # STATISTICAL RESOLUTION OUTLIERS
        # ----------------------------------------------------

        resolution_outliers = (
            self._statistical_anomalies(
                df,
                "resolution_time_hrs",
            )
        )

        for _, row in resolution_outliers.iterrows():

            if self._has_operational_anomaly(
                anomalies,
                row["ticket_id"],
            ):
                continue

            if row["status"] == "Resolved":

                reason = (
                    "Resolution time is significantly "
                    "higher than the normal dataset range. "
                    "The ticket is already resolved, so "
                    "this is classified as a statistical "
                    "outlier rather than an active SLA issue."
                )

            else:

                reason = (
                    "Resolution time is significantly "
                    "higher than the normal dataset range."
                )

            anomalies.append(
                self._create_anomaly(
                    row=row,
                    anomaly_type=(
                        "Unusually long resolution time"
                    ),
                    severity="Medium",
                    reason=reason,
                )
            )

        # ----------------------------------------------------
        # STATISTICAL RESPONSE OUTLIERS
        # ----------------------------------------------------

        response_outliers = (
            self._statistical_anomalies(
                df,
                "response_time_hrs",
            )
        )

        for _, row in response_outliers.iterrows():

            if self._has_operational_anomaly(
                anomalies,
                row["ticket_id"],
            ):
                continue

            if row["status"] == "Resolved":

                reason = (
                    "Response time is significantly "
                    "higher than the normal dataset range. "
                    "The ticket is already resolved, so "
                    "this is classified as a statistical "
                    "outlier."
                )

            else:

                reason = (
                    "Response time is significantly "
                    "higher than the normal dataset range."
                )

            anomalies.append(
                self._create_anomaly(
                    row=row,
                    anomaly_type=(
                        "Unusually long response time"
                    ),
                    severity="Medium",
                    reason=reason,
                )
            )

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        unique_anomalies = {}

        for anomaly in anomalies:

            key = (
                anomaly["ticket_id"],
                anomaly["anomaly_type"],
            )

            unique_anomalies[key] = anomaly

        anomalies = list(
            unique_anomalies.values()
        )

        # ----------------------------------------------------
        # SORT BY SEVERITY
        # ----------------------------------------------------

        severity_order = {
            "Critical": 0,
            "High": 1,
            "Medium": 2,
            "Low": 3,
        }

        anomalies.sort(
            key=lambda item: (
                severity_order.get(
                    item["severity"],
                    99,
                ),
                -(
                    item["resolution_time_hrs"]
                    or 0
                ),
            )
        )

        return {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
        }

    # ========================================================
    # TIME RANGE
    # ========================================================

    def _get_dataset_latest_date(self):

        df = pd.read_sql(
            """
            SELECT MAX(created_at) AS latest_date
            FROM support_tickets
            """,
            self.engine,
        )

        latest_date = pd.to_datetime(
            df.iloc[0]["latest_date"],
            errors="coerce",
        )

        if pd.isna(latest_date):

            raise ValueError(
                "No valid created_at dates found "
                "in the dataset."
            )

        return latest_date

    def _get_time_range(
        self,
        period: str,
    ):

        latest_date = (
            self._get_dataset_latest_date()
        )

        if period == "this_month":

            start_date = latest_date.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            end_date = (
                start_date
                + pd.DateOffset(
                    months=1
                )
            )

        elif period == "this_week":

            start_date = (
                latest_date
                - pd.Timedelta(
                    days=latest_date.weekday()
                )
            )

            start_date = start_date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            end_date = (
                start_date
                + pd.Timedelta(
                    days=7
                )
            )

        else:

            raise ValueError(
                "Unsupported period. "
                "Use this_week or this_month."
            )

        return (
            start_date,
            end_date,
        )

    # ========================================================
    # IQR OUTLIER DETECTION
    # ========================================================

    def _statistical_anomalies(
        self,
        df: pd.DataFrame,
        column: str,
    ) -> pd.DataFrame:

        if df.empty:
            return df.iloc[0:0]

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        if len(values) < 5:
            return df.iloc[0:0]

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        if iqr <= 0:
            return df.iloc[0:0]

        upper_bound = (
            q3 + 1.5 * iqr
        )

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        mask = (
            numeric_values
            > upper_bound
        )

        return df.loc[mask]

    # ========================================================
    # CHECK EXISTING OPERATIONAL ANOMALY
    # ========================================================

    @staticmethod
    def _has_operational_anomaly(
        anomalies: list[dict],
        ticket_id: Any,
    ) -> bool:

        operational_types = {
            "Critical unresolved ticket",
            "High priority unresolved ticket",
            "Long unresolved ticket",
        }

        return any(
            anomaly["ticket_id"] == ticket_id
            and anomaly["anomaly_type"]
            in operational_types
            for anomaly in anomalies
        )

    # ========================================================
    # CREATE ANOMALY OBJECT
    # ========================================================

    @staticmethod
    def _create_anomaly(
        row,
        anomaly_type: str,
        severity: str,
        reason: str,
    ) -> dict[str, Any]:

        created_at = row["created_at"]

        if pd.isna(created_at):

            created_at = None

        else:

            created_at = created_at.isoformat()

        def clean(value):

            if pd.isna(value):
                return None

            if hasattr(value, "item"):

                try:
                    return value.item()
                except Exception:
                    pass

            return value

        return {
            "ticket_id": clean(
                row["ticket_id"]
            ),
            "created_at": created_at,
            "category": clean(
                row["category"]
            ),
            "priority": clean(
                row["priority"]
            ),
            "status": clean(
                row["status"]
            ),
            "response_time_hrs": clean(
                row["response_time_hrs"]
            ),
            "resolution_time_hrs": clean(
                row["resolution_time_hrs"]
            ),
            "agent_id": clean(
                row["agent_id"]
            ),
            "customer_rating": clean(
                row["customer_rating"]
            ),
            "issue_summary": clean(
                row["issue_summary"]
            ),
            "anomaly_type": anomaly_type,
            "severity": severity,
            "reason": reason,
        }