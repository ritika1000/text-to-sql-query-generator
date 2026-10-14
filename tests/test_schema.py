import sqlite3

from text2sql.sample_data import build_database
from text2sql.schema import get_schema


def test_schema_lists_tables_columns_and_foreign_keys(tmp_path):
    db = build_database(tmp_path / "shop.db")
    conn = sqlite3.connect(db)
    schema = get_schema(conn)
    conn.close()

    for table in ["customers", "products", "orders", "order_items"]:
        assert f"Table {table}(" in schema
    assert "orders.customer_id references customers.id" in schema
    assert "order_items.product_id references products.id" in schema
