import requests
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="AI Support Intelligence",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# API HELPERS
# ============================================================

def check_health():

    try:

        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=5,
        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return None


def ask_question(question):

    response = requests.post(
        f"{API_BASE_URL}/query",
        json={
            "question": question
        },
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_anomalies(period=None):

    params = {}

    if period:
        params["period"] = period

    response = requests.get(
        f"{API_BASE_URL}/anomalies",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI Support Intelligence")

st.caption(
    "AI-powered customer support analytics "
    "and anomaly detection"
)


# ============================================================
# API STATUS
# ============================================================

health = check_health()

if health:

    st.success(
        "API connected and database service is healthy."
    )

else:

    st.error(
        "API is not reachable. "
        "Start FastAPI before using the dashboard."
    )


# ============================================================
# TABS
# ============================================================

tab_query, tab_anomaly = st.tabs(
    [
        "💬 Ask Questions",
        "🚨 Anomalies",
    ]
)


# ============================================================
# QUERY TAB
# ============================================================

with tab_query:

    st.subheader(
        "Ask about support tickets"
    )

    st.write(
        "Ask questions in natural language. "
        "The AI converts your question into a "
        "validated database query."
    )

    examples = [
        "How many tickets are currently open?",
        "Which agent resolved the most tickets this month?",
        "Show me all Critical tickets not resolved within 12 hours.",
        "What is the average customer rating for Technical category tickets?",
        "How many tickets were created this week?",
    ]

    selected_example = st.selectbox(
        "Example questions",
        [
            "Select an example..."
        ] + examples,
    )

    question = st.text_area(
        "Your question",
        value=(
            ""
            if selected_example
            == "Select an example..."
            else selected_example
        ),
        height=100,
        placeholder=(
            "Example: How many tickets are currently open?"
        ),
    )

    ask_button = st.button(
        "Ask AI",
        type="primary",
        use_container_width=True,
    )

    if ask_button:

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Analyzing support data..."
            ):

                try:

                    result = ask_question(
                        question.strip()
                    )

                    st.success(
                        result.get(
                            "answer",
                            "No answer returned.",
                        )
                    )

                    data = result.get(
                        "data",
                        [],
                    )

                    if data:

                        st.subheader(
                            "Database Results"
                        )

                        st.dataframe(
                            data,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.info(
                            "No matching records were found."
                        )

                    with st.expander(
                        "View detected AI intent"
                    ):

                        st.json(
                            result.get(
                                "intent",
                                {},
                            )
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"API request failed: {exc}"
                    )

                except Exception as exc:

                    st.error(
                        f"Unexpected error: {exc}"
                    )


# ============================================================
# ANOMALY TAB
# ============================================================

with tab_anomaly:

    st.subheader(
        "Support Ticket Anomalies"
    )

    st.write(
        "Detect operational SLA issues and "
        "statistical outliers in support data."
    )

    period_option = st.selectbox(
        "Time period",
        [
            "All tickets",
            "This week",
            "This month",
        ],
    )

    period_mapping = {
        "All tickets": None,
        "This week": "this_week",
        "This month": "this_month",
    }

    selected_period = period_mapping[
        period_option
    ]

    run_anomaly = st.button(
        "Detect Anomalies",
        type="primary",
        use_container_width=True,
    )

    if run_anomaly:

        with st.spinner(
            "Analyzing ticket anomalies..."
        ):

            try:

                result = get_anomalies(
                    selected_period
                )

                anomalies = result.get(
                    "anomalies",
                    [],
                )

                total = len(anomalies)

                critical = sum(
                    1
                    for item in anomalies
                    if item.get("severity")
                    == "Critical"
                )

                high = sum(
                    1
                    for item in anomalies
                    if item.get("severity")
                    == "High"
                )

                medium = sum(
                    1
                    for item in anomalies
                    if item.get("severity")
                    == "Medium"
                )

                col1, col2, col3, col4 = st.columns(
                    4
                )

                col1.metric(
                    "Total Anomalies",
                    total,
                )

                col2.metric(
                    "Critical",
                    critical,
                )

                col3.metric(
                    "High",
                    high,
                )

                col4.metric(
                    "Medium",
                    medium,
                )

                st.divider()

                if not anomalies:

                    st.success(
                        "No anomalies were detected "
                        "for the selected period."
                    )

                else:

                    st.warning(
                        f"{total} anomaly/anomalies detected."
                    )

                    for index, anomaly in enumerate(
                        anomalies,
                        start=1,
                    ):

                        severity = anomaly.get(
                            "severity",
                            "Unknown",
                        )

                        ticket_id = anomaly.get(
                            "ticket_id",
                            "Unknown",
                        )

                        anomaly_type = anomaly.get(
                            "anomaly_type",
                            "Unknown anomaly",
                        )

                        title = (
                            f"{index}. "
                            f"{ticket_id} — "
                            f"{anomaly_type}"
                        )

                        with st.expander(
                            title
                        ):

                            col1, col2 = st.columns(
                                2
                            )

                            with col1:

                                st.write(
                                    f"**Severity:** "
                                    f"{severity}"
                                )

                                st.write(
                                    f"**Priority:** "
                                    f"{anomaly.get('priority')}"
                                )

                                st.write(
                                    f"**Status:** "
                                    f"{anomaly.get('status')}"
                                )

                                st.write(
                                    f"**Category:** "
                                    f"{anomaly.get('category')}"
                                )

                            with col2:

                                st.write(
                                    f"**Resolution time:** "
                                    f"{anomaly.get('resolution_time_hrs')} hrs"
                                )

                                st.write(
                                    f"**Response time:** "
                                    f"{anomaly.get('response_time_hrs')} hrs"
                                )

                                st.write(
                                    f"**Agent:** "
                                    f"{anomaly.get('agent_id')}"
                                )

                                st.write(
                                    f"**Created:** "
                                    f"{anomaly.get('created_at')}"
                                )

                            st.write(
                                f"**Reason:** "
                                f"{anomaly.get('reason')}"
                            )

                            st.write(
                                f"**Issue:** "
                                f"{anomaly.get('issue_summary')}"
                            )

            except requests.exceptions.RequestException as exc:

                st.error(
                    f"API request failed: {exc}"
                )

            except Exception as exc:

                st.error(
                    f"Unexpected error: {exc}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Support Intelligence • "
    "FastAPI + SQLite + Pandas + Groq + Streamlit"
)
