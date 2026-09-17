import json
import re

from groq import Groq

from app.core.config import settings


class LLMService:

    def __init__(self):

        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = settings.groq_model

    # ========================================================
    # GENERIC GROQ CALL
    # ========================================================

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        max_tokens: int = 1000,
    ) -> str:

        try:

            kwargs = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a customer support "
                            "analytics assistant. "
                            "Follow the requested output "
                            "format exactly. "
                            "Keep reasoning brief and "
                            "prioritize the final answer."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0,
                "max_tokens": max_tokens,
            }

            if json_mode:

                kwargs["response_format"] = {
                    "type": "json_object"
                }

            response = (
                self.client
                .chat
                .completions
                .create(**kwargs)
            )

            if not response.choices:

                raise RuntimeError(
                    "Groq returned no choices."
                )

            choice = response.choices[0]

            message = choice.message

            content = message.content

            if not content:

                finish_reason = (
                    choice.finish_reason
                )

                reasoning_tokens = 0

                usage = getattr(
                    response,
                    "usage",
                    None,
                )

                if usage:

                    details = getattr(
                        usage,
                        "completion_tokens_details",
                        None,
                    )

                    if details:

                        reasoning_tokens = (
                            getattr(
                                details,
                                "reasoning_tokens",
                                0,
                            )
                            or 0
                        )

                raise RuntimeError(
                    "Groq returned no final answer. "
                    f"Finish reason: {finish_reason}. "
                    f"Reasoning tokens: "
                    f"{reasoning_tokens}."
                )

            return content.strip()

        except RuntimeError:

            raise

        except Exception as exc:

            raise RuntimeError(
                f"Groq API request failed: {exc}"
            ) from exc

    # ========================================================
    # CLASSIFY NATURAL LANGUAGE QUESTION
    # ========================================================

    def classify_question(
        self,
        question: str,
    ) -> dict:

        prompt = f"""
Convert this customer support analytics question
into ONE JSON object.

QUESTION:
{question}

AVAILABLE DATABASE COLUMNS:
ticket_id
created_at
category
priority
status
response_time_hrs
resolution_time_hrs
agent_id
customer_rating
issue_summary

VALID CATEGORY VALUES:
Billing
Technical
General

VALID PRIORITY VALUES:
Low
Medium
High
Critical

VALID STATUS VALUES:
Open
Resolved
Escalated

VALID INTENTS:
count
average
sum
minimum
maximum
group_count
group_average
list
anomaly

VALID OPERATORS:
=
!=
>
>=
<
<=

VALID TIME PERIODS:
null
this_week
this_month

OUTPUT FORMAT:

{{
  "intent": "count",
  "filters": [],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

FILTER FORMAT:

{{
  "column": "status",
  "operator": "=",
  "value": "Open"
}}

IMPORTANT RULES:

1. Return exactly ONE valid JSON object.

2. Do not return markdown.

3. Do not return ```json.

4. Do not explain anything.

5. Do not generate SQL.

6. Use only the database columns listed above.

7. "open" means status = Open.

8. "resolved" means status = Resolved.

9. "unresolved" means status != Resolved.

10. "critical" means priority = Critical.

11. "high priority" means priority = High.

12. "technical" means category = Technical.

13. "billing" means category = Billing.

14. "general" means category = General.

15. "most" means order = desc.

16. "least" means order = asc.

17. "more than X" means > X.

18. "greater than X" means > X.

19. "over X" means > X.

20. "less than X" means < X.

21. "under X" means < X.

22. "at least X" means >= X.

23. "at most X" means <= X.

24. "within X hours" means <= X.

25. "this week" means time_period = this_week.

26. "this month" means time_period = this_month.

27. If no time period is mentioned,
    time_period = null.

28. Time periods must NOT be placed
    inside filters.

29. If the question asks for average
    customer rating:

    intent = average
    aggregation = customer_rating

30. If the question asks for average
    resolution time:

    intent = average
    aggregation = resolution_time_hrs

31. If the question asks for average
    response time:

    intent = average
    aggregation = response_time_hrs

32. If the question asks "which agent":

    intent = group_count
    group_by = agent_id

33. If the question asks "by agent":

    group_by = agent_id

34. If the question asks "how many":

    intent = count

35. If the question asks for a list
    or "show me tickets":

    intent = list

36. filters must always be an array.

37. aggregation must be null when
    aggregation is not required.

38. group_by must be null when
    grouping is not required.

39. time_period must be either:

    null
    this_week
    this_month

40. limit must be between 1 and 100.

41. Do not invent database columns.

42. Do not invent category values.

43. Do not invent priority values.

44. Do not invent status values.

EXAMPLES:

Question:
How many tickets are currently open?

JSON:
{{
  "intent": "count",
  "filters": [
    {{
      "column": "status",
      "operator": "=",
      "value": "Open"
    }}
  ],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

Question:
How many Technical tickets are there?

JSON:
{{
  "intent": "count",
  "filters": [
    {{
      "column": "category",
      "operator": "=",
      "value": "Technical"
    }}
  ],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

Question:
What is the average customer rating
for Technical tickets?

JSON:
{{
  "intent": "average",
  "filters": [
    {{
      "column": "category",
      "operator": "=",
      "value": "Technical"
    }}
  ],
  "aggregation": "customer_rating",
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

Question:
Which agent resolved the most tickets?

JSON:
{{
  "intent": "group_count",
  "filters": [
    {{
      "column": "status",
      "operator": "=",
      "value": "Resolved"
    }}
  ],
  "aggregation": null,
  "group_by": "agent_id",
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

Question:
Which agent resolved the most tickets this month?

JSON:
{{
  "intent": "group_count",
  "filters": [
    {{
      "column": "status",
      "operator": "=",
      "value": "Resolved"
    }}
  ],
  "aggregation": null,
  "group_by": "agent_id",
  "order": "desc",
  "limit": 100,
  "time_period": "this_month"
}}

Question:
How many tickets were created this week?

JSON:
{{
  "intent": "count",
  "filters": [],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": "this_week"
}}

Question:
Show unresolved Critical tickets this month.

JSON:
{{
  "intent": "list",
  "filters": [
    {{
      "column": "priority",
      "operator": "=",
      "value": "Critical"
    }},
    {{
      "column": "status",
      "operator": "!=",
      "value": "Resolved"
    }}
  ],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": "this_month"
}}

Question:
Show Critical tickets not resolved within 12 hours.

JSON:
{{
  "intent": "list",
  "filters": [
    {{
      "column": "priority",
      "operator": "=",
      "value": "Critical"
    }},
    {{
      "column": "status",
      "operator": "!=",
      "value": "Resolved"
    }},
    {{
      "column": "resolution_time_hrs",
      "operator": ">",
      "value": 12
    }}
  ],
  "aggregation": null,
  "group_by": null,
  "order": "desc",
  "limit": 100,
  "time_period": null
}}

NOW RETURN ONLY THE JSON OBJECT.
"""

        raw_response = self.generate(
            prompt,
            json_mode=False,
            max_tokens=1200,
        )

        return self._parse_json(
            raw_response
        )

    # ========================================================
    # JSON PARSER
    # ========================================================

    @staticmethod
    def _parse_json(
        response: str,
    ) -> dict:

        if not response:

            raise ValueError(
                "Groq returned an empty JSON response."
            )

        response = response.strip()

        # Remove markdown code fences
        response = re.sub(
            r"^```(?:json)?\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"\s*```$",
            "",
            response,
        )

        response = response.strip()

        # Try parsing the complete response
        try:

            result = json.loads(
                response
            )

            if not isinstance(
                result,
                dict,
            ):

                raise ValueError(
                    "Groq response is not a JSON object."
                )

            return result

        except json.JSONDecodeError:

            pass

        # Try extracting JSON from extra text
        start = response.find("{")
        end = response.rfind("}")

        if (
            start != -1
            and end != -1
            and end > start
        ):

            json_text = response[
                start:end + 1
            ]

            try:

                result = json.loads(
                    json_text
                )

                if isinstance(
                    result,
                    dict,
                ):

                    return result

            except json.JSONDecodeError:

                pass

        raise ValueError(
            "Groq returned invalid JSON: "
            f"{response}"
        )