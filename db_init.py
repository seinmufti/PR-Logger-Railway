import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS pr_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pr_no INTEGER NOT NULL,
    title TEXT NOT NULL,
    currency TEXT NOT NULL,
    budget_line TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    total_cost REAL NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0,
    revision TEXT NOT NULL DEFAULT '{"type": "none", "changes": {}}'
);
CREATE TABLE IF NOT EXISTS pr_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pr_id INTEGER NOT NULL,
    "index" INTEGER NOT NULL,
    description TEXT NOT NULL,
    cost REAL NOT NULL,
    quantity INTEGER NOT NULL,
    total REAL NOT NULL,
    revision TEXT NOT NULL DEFAULT '{"type": "none", "changes": {}}',
    FOREIGN KEY (pr_id) REFERENCES pr_logs(id)
);
CREATE TABLE IF NOT EXISTS pr_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pr_id INTEGER NOT NULL,
    datetime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pr_id) REFERENCES pr_logs(id)
);
"""


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
