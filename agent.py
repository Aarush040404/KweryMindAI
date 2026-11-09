import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Keep these at the top so changes are one-line fixes
MODEL_NAME = "qwen/qwen3.8-27b"   # check this exists in Groq's model list
DB_PATH = "data/Chinook_Sqlite.sqlite"

_schema_cache = None


def get_connection(db_path=DB_PATH):
    """Opens the database in read-only mode."""
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_database_schema(db_path=DB_PATH):
    """Builds a text blueprint of tables, columns, types, keys and foreign keys."""
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row[0] for row in cursor.fetchall()]

    schema_text = "Database Schema:\n\n"
    for table in tables:
        schema_text += f"Table: {table}\n"

        # col = (cid, name, type, notnull, default, pk)
        cursor.execute(f'PRAGMA table_info("{table}");')
        cols = []
        for col in cursor.fetchall():
            desc = f"{col[1]} ({col[2]})"
            if col[5]:
                desc += " PRIMARY KEY"
            cols.append(desc)
        schema_text += f"Columns: {', '.join(cols)}\n"

        # fk = (id, seq, target_table, from_col, to_col, ...)
        cursor.execute(f'PRAGMA foreign_key_list("{table}");')
        fks = cursor.fetchall()
        if fks:
            fk_list = [f"{fk[3]} -> {fk[2]}.{fk[4]}" for fk in fks]
            schema_text += f"Foreign Keys: {', '.join(fk_list)}\n"

        schema_text += "\n"

    conn.close()
    _schema_cache = schema_text
    return schema_text


def clean_sql(text):
    """Strips <think> blocks and markdown fences from the model output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```(?:sql)?", "", text)
    return text.strip()


def generate_sql(question, use_schema=True):
    """Generates SQL with or without the schema context."""
    if use_schema:
        schema = get_database_schema()
        prompt = (
            f"Given this SQLite database schema:\n{schema}\n\n"
            f"Write a SQL query for this request: {question}\n"
            "Return ONLY the raw SQL code, no markdown, no explanation."
        )
    else:
        prompt = (
            f"Write a SQL query for this request: {question}\n"
            "Return ONLY the raw SQL code, no markdown, no explanation."
        )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL_NAME,
        temperature=0,   # same question -> same SQL, needed for a fair eval
    )
    return clean_sql(response.choices[0].message.content)


if __name__ == "__main__":
    # Make sure this customer exists before trusting the result
    test_question = "List all the tracks purchased by the customer 'Tim Goyer'."

    print("=== BASELINE (NO SCHEMA) ===")
    print(generate_sql(test_question, use_schema=False))

    print("\n=== GROUNDED (WITH SCHEMA) ===")
    print(generate_sql(test_question, use_schema=True))