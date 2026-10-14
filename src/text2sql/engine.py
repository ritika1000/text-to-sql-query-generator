"""Core logic: question -> prompt -> LLM -> safety check -> run on DB -> retry on error."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

from .guard import clean_sql, validate_sql
from .schema import get_schema

SYSTEM_PROMPT = """You are an expert SQLite analyst.
Given the database schema below, write ONE SQLite SELECT query that answers the user's question.
Rules:
- Return ONLY the SQL query. No explanation, no markdown.
- Use only the tables and columns in the schema.
- Never modify data.

Schema:
{schema}"""


@dataclass
class Result:
    question: str
    sql: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    error: str | None = None
    attempts: int = 0

    @property
    def ok(self) -> bool:
        return self.error is None


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open the database in read-only mode so writes are impossible at the DB level too."""
    return sqlite3.connect(f"{Path(db_path).resolve().as_uri()}?mode=ro", uri=True)


class TextToSQL:
    def __init__(self, db_path, llm, max_rows: int = 100, max_retries: int = 1):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.llm = llm
        self.max_rows = max_rows
        self.max_retries = max_retries
        with closing(connect_readonly(self.db_path)) as conn:
            self.schema = get_schema(conn)

    def _execute(self, sql: str) -> tuple[list[str], list[tuple]]:
        with closing(connect_readonly(self.db_path)) as conn:
            cursor = conn.execute(sql)
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(self.max_rows)
        return columns, rows

    def ask(self, question: str) -> Result:
        result = Result(question=question)
        if not question.strip():
            result.error = "Please type a question."
            return result

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(schema=self.schema)},
            {"role": "user", "content": question},
        ]

        for attempt in range(1, self.max_retries + 2):
            result.attempts = attempt
            raw = self.llm.complete(messages)
            result.sql = clean_sql(raw)
            try:
                validate_sql(result.sql)
                result.columns, result.rows = self._execute(result.sql)
                result.error = None
                return result
            except (ValueError, sqlite3.Error) as exc:
                result.error = str(exc)
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": f"That query failed: {exc}. "
                        "Fix it and return only the corrected SQL.",
                    }
                )
        return result
