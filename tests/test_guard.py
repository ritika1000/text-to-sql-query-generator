import pytest

from text2sql.guard import clean_sql, validate_sql


def test_clean_sql_removes_fences_and_semicolon():
    raw = "```sql\nSELECT * FROM customers;\n```"
    assert clean_sql(raw) == "SELECT * FROM customers"


def test_clean_sql_plain_text_untouched():
    assert clean_sql("  SELECT 1  ") == "SELECT 1"


@pytest.mark.parametrize(
    "sql",
    ["SELECT * FROM customers", "select count(*) from orders", "WITH t AS (SELECT 1) SELECT * FROM t"],
)
def test_valid_queries_pass(sql):
    validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "DROP TABLE customers",
        "DELETE FROM orders",
        "UPDATE products SET price = 0",
        "INSERT INTO customers VALUES (1, 'a', 'b', 'c')",
        "SELECT 1; DROP TABLE customers",
        "SELECT * FROM customers -- sneaky",
        "SELECT * FROM customers /* hi */",
        "PRAGMA table_info(customers)",
        "SELECT * FROM customers WHERE 1=1 UNION SELECT 1 FROM x; DELETE FROM x",
    ],
)
def test_unsafe_queries_rejected(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)
