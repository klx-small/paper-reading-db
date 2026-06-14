import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from utils import DEFAULT_VALUES, TEXT_COLUMNS, normalize_import_dataframe


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str(BASE_DIR / "data" / "papers.db")


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def get_connection(db_path=DATABASE_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def open_database(db_path=DATABASE_PATH):
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(db_path=DATABASE_PATH):
    column_sql = ",\n        ".join(f"{quote_identifier(column)} TEXT" for column in TEXT_COLUMNS)
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {column_sql}
    )
    """

    with open_database(db_path) as conn:
        conn.execute(create_sql)
        existing_columns = [row["name"] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        for column in TEXT_COLUMNS:
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE papers ADD COLUMN {quote_identifier(column)} TEXT")


def normalize_paper_payload(data):
    normalized = {}
    for column in TEXT_COLUMNS:
        value = data.get(column, DEFAULT_VALUES.get(column, ""))
        if pd.isna(value):
            value = ""
        value = str(value).strip()
        if value == "" and column in DEFAULT_VALUES:
            value = DEFAULT_VALUES[column]
        normalized[column] = value
    return normalized


def add_paper(data, db_path=DATABASE_PATH):
    init_db(db_path)
    payload = normalize_paper_payload(data)
    columns = list(payload.keys())
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(quote_identifier(column) for column in columns)

    with open_database(db_path) as conn:
        cursor = conn.execute(
            f"INSERT INTO papers ({quoted_columns}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        return cursor.lastrowid


def update_paper(paper_id, data, db_path=DATABASE_PATH):
    init_db(db_path)
    updates = {}
    for column, value in data.items():
        if column not in TEXT_COLUMNS:
            continue
        if pd.isna(value):
            value = ""
        value = str(value).strip()
        if value == "" and column in DEFAULT_VALUES:
            value = DEFAULT_VALUES[column]
        updates[column] = value

    if not updates:
        return

    assignments = ", ".join(f"{quote_identifier(column)} = ?" for column in updates)
    values = list(updates.values()) + [paper_id]

    with open_database(db_path) as conn:
        conn.execute(f"UPDATE papers SET {assignments} WHERE id = ?", values)


def delete_paper(paper_id, db_path=DATABASE_PATH):
    init_db(db_path)
    with open_database(db_path) as conn:
        conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))


def get_all_papers(db_path=DATABASE_PATH):
    init_db(db_path)
    with open_database(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM papers ORDER BY id DESC", conn)

    columns = ["id"] + TEXT_COLUMNS
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df[columns]


def get_paper(paper_id, db_path=DATABASE_PATH):
    init_db(db_path)
    with open_database(db_path) as conn:
        row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    return dict(row) if row else None


def search_papers(topic="", keyword="", status="", db_path=DATABASE_PATH):
    df = get_all_papers(db_path)
    if topic:
        df = df[df["研究主题"].fillna("").str.contains(topic, case=False, na=False)]
    if keyword:
        keyword_columns = ["论文标题", "作者", "关键词", "一句话概括", "备注"]
        mask = pd.Series(False, index=df.index)
        for column in keyword_columns:
            mask = mask | df[column].fillna("").str.contains(keyword, case=False, na=False)
        df = df[mask]
    if status:
        df = df[df["阅读状态"] == status]
    return df.reset_index(drop=True)


def import_papers_from_dataframe(df, db_path=DATABASE_PATH):
    normalized = normalize_import_dataframe(df)
    imported_count = 0
    for _, row in normalized.iterrows():
        add_paper(row.to_dict(), db_path)
        imported_count += 1
    return imported_count
