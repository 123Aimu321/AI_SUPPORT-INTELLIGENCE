from typing import Any

import pandas as pd

from sqlalchemy import create_engine, text

from app.core.config import settings

from app.services.llm_service import LLMService

from app.utils.sql_validator import validate_intent


class QueryService:

    def __init__(self):

        self.llm = LLMService()

        self.engine = create_engine(
            settings.database_url,
            connect_args={
                "check_same_thread": False
            },
        )

    # ========================================================
    # MAIN QUESTION ANSWER
    # ========================================================

    def answer_question(
        self,
        question: str,
    ) -> dict[str, Any]:

        intent = self.llm.classify_question(
            question
        )

        intent = validate_intent(
            intent
        )

        sql, parameters = (
            self._build_query(
                intent
            )
        )

        rows = self._execute_query(
            sql,
            parameters,
        )

        answer = self._generate_answer(
            question,
            rows,
            intent,
        )

        return {
            "question": question,
            "answer": answer,
            "data": rows,
            "intent": intent,
        }

    # ========================================================
    # BUILD SQL
    # ========================================================

    def _build_query(
        self,
        intent: dict,
    ):

        query_intent = intent[
            "intent"
        ]

        filters = intent.get(
            "filters",
            [],
        )

        aggregation = intent.get(
            "aggregation"
        )

        group_by = intent.get(
            "group_by"
        )

        order = intent.get(
            "order",
            "desc",
        )

        limit = intent.get(
            "limit",
            100,
        )

        time_period = intent.get(
            "time_period"
        )

        conditions = []

        parameters = {}

        # ====================================================
        # NORMAL FILTERS
        # ====================================================

        for index, filter_item in enumerate(
            filters
        ):

            column = filter_item[
                "column"
            ]

            operator = filter_item[
                "operator"
            ]

            value = filter_item[
                "value"
            ]

            parameter_name = (
                f"filter_{index}"
            )

            conditions.append(
                f'"{column}" {operator} '
                f':{parameter_name}'
            )

            parameters[
                parameter_name
            ] = value

        # ====================================================
        # TIME FILTER
        # ====================================================

        if time_period:

            start_date, end_date = (
                self._get_time_range(
                    time_period
                )
            )

            conditions.append(
                '"created_at" >= :start_date'
            )

            conditions.append(
                '"created_at" < :end_date'
            )

            parameters[
                "start_date"
            ] = start_date

            parameters[
                "end_date"
            ] = end_date

        # ====================================================
        # WHERE
        # ====================================================

        where_clause = ""

        if conditions:

            where_clause = (
                " WHERE "
                + " AND ".join(
                    conditions
                )
            )

        # ====================================================
        # COUNT
        # ====================================================

        if query_intent == "count":

            sql = f"""
                SELECT COUNT(*) AS count
                FROM support_tickets
                {where_clause}
            """

        # ====================================================
        # AVERAGE
        # ====================================================

        elif query_intent == "average":

            if not aggregation:

                raise ValueError(
                    "Aggregation is required."
                )

            sql = f"""
                SELECT
                    AVG("{aggregation}") AS average
                FROM support_tickets
                {where_clause}
            """

        # ====================================================
        # SUM
        # ====================================================

        elif query_intent == "sum":

            if not aggregation:

                raise ValueError(
                    "Aggregation is required."
                )

            sql = f"""
                SELECT
                    SUM("{aggregation}") AS total
                FROM support_tickets
                {where_clause}
            """

        # ====================================================
        # MINIMUM
        # ====================================================

        elif query_intent == "minimum":

            if not aggregation:

                raise ValueError(
                    "Aggregation is required."
                )

            sql = f"""
                SELECT
                    MIN("{aggregation}") AS minimum
                FROM support_tickets
                {where_clause}
            """

        # ====================================================
        # MAXIMUM
        # ====================================================

        elif query_intent == "maximum":

            if not aggregation:

                raise ValueError(
                    "Aggregation is required."
                )

            sql = f"""
                SELECT
                    MAX("{aggregation}") AS maximum
                FROM support_tickets
                {where_clause}
            """

        # ====================================================
        # GROUP COUNT
        # ====================================================

        elif query_intent == "group_count":

            if not group_by:

                raise ValueError(
                    "group_by is required."
                )

            sql = f"""
                SELECT
                    "{group_by}" AS group_value,
                    COUNT(*) AS count
                FROM support_tickets
                {where_clause}
                GROUP BY "{group_by}"
                ORDER BY count {order}
                LIMIT :limit
            """

            parameters[
                "limit"
            ] = limit

        # ====================================================
        # GROUP AVERAGE
        # ====================================================

        elif query_intent == "group_average":

            if not group_by:

                raise ValueError(
                    "group_by is required."
                )

            if not aggregation:

                raise ValueError(
                    "aggregation is required."
                )

            sql = f"""
                SELECT
                    "{group_by}" AS group_value,
                    AVG("{aggregation}") AS average
                FROM support_tickets
                {where_clause}
                GROUP BY "{group_by}"
                ORDER BY average {order}
                LIMIT :limit
            """

            parameters[
                "limit"
            ] = limit

        # ====================================================
        # LIST
        # ====================================================

        elif query_intent == "list":

            sql = f"""
                SELECT
                    ticket_id,
                    created_at,
                    category,
                    priority,
                    status,
                    response_time_hrs,
                    resolution_time_hrs,
                    agent_id,
                    customer_rating,
                    issue_summary
                FROM support_tickets
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
            """

            parameters[
                "limit"
            ] = limit

        # ====================================================
        # ANOMALY
        # ====================================================

        elif query_intent == "anomaly":

            raise ValueError(
                "Use the /anomalies endpoint "
                "for anomaly detection."
            )

        else:

            raise ValueError(
                f"Unsupported query intent: "
                f"{query_intent}"
            )

        return (
            sql,
            parameters,
        )

    # ========================================================
    # DATASET TIME RANGE
    # ========================================================

    def _get_dataset_latest_date(self):

        sql = """
            SELECT MAX(created_at)
            AS latest_date
            FROM support_tickets
        """

        with self.engine.connect() as connection:

            result = connection.execute(
                text(sql)
            ).scalar()

        if result is None:

            raise ValueError(
                "No created_at dates found "
                "in the dataset."
            )

        return pd.Timestamp(
            result
        )

    # ========================================================
    # THIS WEEK / THIS MONTH
    # ========================================================

    def _get_time_range(
        self,
        time_period: str,
    ):

        latest_date = (
            self._get_dataset_latest_date()
        )

        # ----------------------------------------------------
        # THIS MONTH
        # ----------------------------------------------------

        if time_period == "this_month":

            start_date = (
                latest_date
                .replace(
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            )

            end_date = (
                start_date
                + pd.DateOffset(
                    months=1
                )
            )

        # ----------------------------------------------------
        # THIS WEEK
        # ----------------------------------------------------

        elif time_period == "this_week":

            start_date = (
                latest_date
                - pd.Timedelta(
                    days=latest_date.weekday()
                )
            )

            start_date = (
                start_date
                .replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            )

            end_date = (
                start_date
                + pd.Timedelta(
                    days=7
                )
            )

        else:

            raise ValueError(
                f"Unsupported time period: "
                f"{time_period}"
            )

        return (
            start_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    # ========================================================
    # EXECUTE QUERY
    # ========================================================

    def _execute_query(
        self,
        sql: str,
        parameters: dict,
    ) -> list[dict]:

        with self.engine.connect() as connection:

            result = connection.execute(
                text(sql),
                parameters,
            )

            rows = (
                result
                .mappings()
                .all()
            )

        return [
            {
                key: self._clean_value(
                    value
                )
                for key, value in row.items()
            }
            for row in rows
        ]

    # ========================================================
    # CLEAN VALUES
    # ========================================================

    @staticmethod
    def _clean_value(
        value
    ):

        if value is None:

            return None

        if hasattr(
            value,
            "item",
        ):

            try:

                return value.item()

            except Exception:

                pass

        return value

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    def _generate_answer(
        self,
        question: str,
        rows: list[dict],
        intent: dict,
    ) -> str:

        preview_rows = rows[:10]

        result_summary = {
            "returned_records": len(rows),
            "preview": preview_rows,
        }

        time_period = intent.get(
            "time_period"
        )

        prompt = f"""
Answer this support analytics question.

QUESTION:
{question}

QUERY TYPE:
{intent.get("intent")}

TIME PERIOD:
{time_period}

DATABASE RESULT:
{result_summary}

RULES:
- Use only the database result.
- Never invent facts.
- Never change numbers.
- Be concise.
- Do not mention SQL.
- Do not return JSON.
- If there are no records, say no matching records were found.
- Return only the answer.
"""

        return self.llm.generate(
            prompt,
            json_mode=False,
            max_tokens=300,
        )