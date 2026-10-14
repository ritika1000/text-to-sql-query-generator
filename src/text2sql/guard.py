"""Safety layer: only a single, read-only SELECT query is ever allowed to run."""

from __future__ import annotations

import re

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|truncate)\b",
    re.IGNORECASE,
)


def clean_sql(raw: str) -> str:
    """Strip markdown code fences and the trailing semicolon that LLMs often add."""
    text = raw.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip().rstrip(";").strip()


def validate_sql(sql: str) -> None:
    """Raise ValueError if the query is not a safe single SELECT."""
    if not sql:
        raise ValueError("The model returned an empty query.")
    if ";" in sql:
        raise ValueError("Only one SQL statement is allowed.")
    if "--" in sql or "/*" in sql:
        raise ValueError("SQL comments are not allowed.")
    if not re.match(r"^(select|with)\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    match = FORBIDDEN.search(sql)
    if match:
        raise ValueError(f"Forbidden keyword in query: {match.group(0).upper()}")
