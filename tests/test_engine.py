import sqlite3

import pytest

from text2sql.cli import format_table
from text2sql.engine import TextToSQL
from text2sql.llm import LLMClient
from text2sql.sample_data import build_database


class FakeLLM:
    """Returns pre-set replies one by one and records the messages it was sent."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, messages):
        self.calls.append([dict(m) for m in messages])
        return self.replies.pop(0)


@pytest.fixture
def db(tmp_path):
    return build_database(tmp_path / "shop.db")


def test_happy_path_returns_rows(db):
    llm = FakeLLM(["```sql\nSELECT COUNT(*) AS n FROM customers;\n```"])
    result = TextToSQL(db, llm).ask("How many customers are there?")
    assert result.ok and result.attempts == 1
    assert result.columns == ["n"] and result.rows == [(50,)]


def test_schema_is_included_in_prompt(db):
    llm = FakeLLM(["SELECT 1"])
    TextToSQL(db, llm).ask("anything")
    assert "Table customers(" in llm.calls[0][0]["content"]


def test_retries_after_sql_error_and_succeeds(db):
    llm = FakeLLM(["SELECT * FROM customer", "SELECT COUNT(*) FROM customers"])
    result = TextToSQL(db, llm).ask("count customers")
    assert result.ok and result.attempts == 2
    # the error message was fed back to the model for the 2nd attempt
    assert "no such table" in llm.calls[1][-1]["content"]


def test_gives_up_after_max_retries(db):
    llm = FakeLLM(["SELECT * FROM nope", "SELECT * FROM still_nope"])
    result = TextToSQL(db, llm, max_retries=1).ask("q")
    assert not result.ok and result.attempts == 2


def test_dangerous_query_is_blocked_and_data_survives(db):
    llm = FakeLLM(["DROP TABLE customers", "DELETE FROM customers"])
    result = TextToSQL(db, llm).ask("delete everything")
    assert not result.ok
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 50
    conn.close()


def test_database_connection_is_really_read_only(db):
    from text2sql.engine import connect_readonly

    conn = connect_readonly(db)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM customers")
    conn.close()


def test_max_rows_limits_output(db):
    llm = FakeLLM(["SELECT * FROM orders"])
    result = TextToSQL(db, llm, max_rows=5).ask("all orders")
    assert len(result.rows) == 5


def test_empty_question_skips_llm(db):
    llm = FakeLLM([])
    result = TextToSQL(db, llm).ask("   ")
    assert not result.ok and llm.calls == []


def test_missing_database_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        TextToSQL(tmp_path / "nope.db", FakeLLM([]))


def test_llm_client_reports_missing_settings(monkeypatch):
    for name in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError):
        LLMClient().complete([{"role": "user", "content": "hi"}])


def test_format_table_aligns_columns():
    text = format_table(["city", "n"], [("Delhi", 12), ("Pune", 3)])
    lines = text.splitlines()
    assert lines[0].startswith("city") and "Delhi" in lines[2]
    assert format_table(["a"], []) == "(no rows)"
