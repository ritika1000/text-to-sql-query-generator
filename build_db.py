"""Create the sample shop database: python build_db.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from text2sql.sample_data import build_database  # noqa: E402

if __name__ == "__main__":
    path = build_database("data/shop.db")
    print(f"Sample database created at {path}")
