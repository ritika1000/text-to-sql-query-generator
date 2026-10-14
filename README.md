# Text-to-SQL Assistant

Ask questions about a SQL database in plain English. The app asks an LLM to write the SQL, checks that the query is safe,
runs it on a **read-only** connection, and shows the result. If the query fails, the error is sent back to the LLM so it can fix its own mistake.

Works with **any OpenAI-compatible API** (Gemini, Groq, OpenRouter, ...), so you can use whichever free tier you like.

## How it works

```
question -> prompt (schema + rules) -> LLM -> clean_sql -> validate_sql (SELECT only)
                                                                |
        result table  <-  run on read-only SQLite  <-----------+
                                |
                     error? -> send error back to LLM -> retry once
```

## Project structure

```
build_db.py              create the sample e-commerce database
main.py                  start the chat app
src/text2sql/
  schema.py              reads tables / columns / foreign keys as text
  guard.py               safety checks (single SELECT only)
  llm.py                 OpenAI-compatible LLM client
  engine.py              the main logic (TextToSQL class)
  cli.py                 chat loop + table formatting
  sample_data.py         builds the demo database (customers, products, orders, order_items)
tests/                   27 pytest tests (LLM is faked, so they run offline)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in key, base URL and model
python build_db.py                 # creates data/shop.db
python main.py
```

Try: `How many customers are from Delhi?` / `Top 5 products by revenue` / `Monthly number of delivered orders in 2025`

Type `schema` to see the tables, `exit` to quit.

## Use your own database

Any SQLite file works: `python main.py --db path/to/your.db`

## Tests

```bash
pytest
```

## Safety design (defence in depth)

1. Prompt tells the model to return one SELECT only
2. `validate_sql` rejects anything that is not a single SELECT/WITH query, or contains write keywords or comments
3. The database is opened in read-only mode, so even a missed check cannot change data
4. Results are capped at 100 rows

Known limitation: the keyword check can reject a harmless query that has a word like "update" inside a text value.
