"""Command-line chat loop."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from .engine import TextToSQL
from .llm import LLMClient


def format_table(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(no rows)"
    table = [list(map(str, columns))] + [[str(v) for v in row] for row in rows]
    widths = [max(len(r[i]) for r in table) for i in range(len(columns))]

    def line(row):
        return " | ".join(cell.ljust(w) for cell, w in zip(row, widths))

    separator = "-+-".join("-" * w for w in widths)
    return "\n".join([line(table[0]), separator] + [line(r) for r in table[1:]])


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Ask your database questions in plain English.")
    parser.add_argument("--db", default="data/shop.db", help="Path to a SQLite database")
    args = parser.parse_args()

    try:
        engine = TextToSQL(args.db, LLMClient())
    except FileNotFoundError as exc:
        print(f"{exc}\nRun `python build_db.py` first to create the sample database.")
        return

    print("Ask a question about the database. Type 'schema' to see tables, 'exit' to quit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question.lower() == "schema":
            print(engine.schema, "\n")
            continue
        if not question:
            continue

        try:
            result = engine.ask(question)
        except Exception as exc:  # network / API-key problems
            print(f"\nCould not reach the LLM: {exc}\n")
            continue

        print(f"\nSQL: {result.sql}")
        if result.ok:
            print(format_table(result.columns, result.rows), "\n")
        else:
            print(f"Sorry, I couldn't answer that: {result.error}\n")


if __name__ == "__main__":
    main()
