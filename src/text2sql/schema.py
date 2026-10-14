"""Read the database structure (tables, columns, foreign keys) as text for the LLM prompt."""

from __future__ import annotations

import sqlite3


def get_schema(conn: sqlite3.Connection) -> str:
    tables = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    lines = []
    for (table,) in tables:
        columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        column_text = ", ".join(f"{col[1]} {col[2]}" for col in columns)
        lines.append(f"Table {table}({column_text})")

        for fk in conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall():
            lines.append(f"  -- {table}.{fk[3]} references {fk[2]}.{fk[4]}")

    return "\n".join(lines)
