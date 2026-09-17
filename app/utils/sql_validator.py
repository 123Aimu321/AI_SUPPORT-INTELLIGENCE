ALLOWED_COLUMNS = {
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


ALLOWED_FILTER_COLUMNS = ALLOWED_COLUMNS


ALLOWED_AGGREGATIONS = {
    "ticket_id",
    "response_time_hrs",
    "resolution_time_hrs",
    "customer_rating",
}


ALLOWED_GROUP_COLUMNS = {
    "category",
    "priority",
    "status",
    "agent_id",
}


ALLOWED_OPERATORS = {
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
}


ALLOWED_TIME_PERIODS = {
    None,
    "this_week",
    "this_month",
}


def validate_intent(
    intent: dict
) -> dict:

    if not isinstance(
        intent,
        dict,
    ):

        raise ValueError(
            "LLM intent must be an object."
        )

    allowed_intents = {
        "count",
        "average",
        "sum",
        "minimum",
        "maximum",
        "group_count",
        "group_average",
        "list",
        "anomaly",
    }

    query_intent = intent.get(
        "intent"
    )

    if query_intent not in allowed_intents:

        raise ValueError(
            f"Unsupported query intent: "
            f"{query_intent}"
        )

    # ========================================================
    # FILTERS
    # ========================================================

    filters = intent.get(
        "filters",
        [],
    )

    if not isinstance(
        filters,
        list,
    ):

        raise ValueError(
            "Filters must be a list."
        )

    validated_filters = []

    for filter_item in filters:

        if not isinstance(
            filter_item,
            dict,
        ):

            raise ValueError(
                "Each filter must be an object."
            )

        column = filter_item.get(
            "column"
        )

        operator = filter_item.get(
            "operator",
            "=",
        )

        if column not in ALLOWED_FILTER_COLUMNS:

            raise ValueError(
                f"Invalid filter column: "
                f"{column}"
            )

        if operator not in ALLOWED_OPERATORS:

            raise ValueError(
                f"Invalid filter operator: "
                f"{operator}"
            )

        if "value" not in filter_item:

            raise ValueError(
                f"Missing filter value for "
                f"{column}"
            )

        validated_filters.append(
            {
                "column": column,
                "operator": operator,
                "value": filter_item["value"],
            }
        )

    # ========================================================
    # AGGREGATION
    # ========================================================

    aggregation = intent.get(
        "aggregation"
    )

    if (
        aggregation is not None
        and aggregation
        not in ALLOWED_AGGREGATIONS
    ):

        raise ValueError(
            f"Invalid aggregation column: "
            f"{aggregation}"
        )

    # ========================================================
    # GROUP BY
    # ========================================================

    group_by = intent.get(
        "group_by"
    )

    if (
        group_by is not None
        and group_by
        not in ALLOWED_GROUP_COLUMNS
    ):

        raise ValueError(
            f"Invalid group-by column: "
            f"{group_by}"
        )

    # ========================================================
    # ORDER
    # ========================================================

    order = intent.get(
        "order",
        "desc",
    )

    if order not in {
        "asc",
        "desc",
    }:

        raise ValueError(
            f"Invalid order: {order}"
        )

    # ========================================================
    # LIMIT
    # ========================================================

    limit = intent.get(
        "limit",
        100,
    )

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError,
    ):

        limit = 100

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    # ========================================================
    # TIME PERIOD
    # ========================================================

    time_period = intent.get(
        "time_period"
    )

    if time_period not in ALLOWED_TIME_PERIODS:

        raise ValueError(
            f"Invalid time period: "
            f"{time_period}"
        )

    # ========================================================
    # FINAL INTENT
    # ========================================================

    intent["filters"] = (
        validated_filters
    )

    intent["limit"] = limit

    intent["order"] = order

    intent["time_period"] = (
        time_period
    )

    return intent