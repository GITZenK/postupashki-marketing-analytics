import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "marketing.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)

    connection = get_connection()

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            channel TEXT NOT NULL,
            start_at TEXT,
            end_at TEXT,
            budget REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS placements (
            placement_id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            channel_name TEXT,
            creative_id TEXT,
            published_at TEXT,
            cost REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id TEXT UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            placement_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (placement_id) REFERENCES placements(placement_id)
        );

        CREATE TABLE IF NOT EXISTS managers (
            manager_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leads (
            lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            manager_id TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (manager_id) REFERENCES managers(manager_id)
        );

        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lead_id INTEGER,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            purchased_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
        );
    """)
    connection.execute(
    """
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        amount REAL NOT NULL,
        course TEXT NOT NULL,
        purchased_at TEXT NOT NULL
    )
    """
    )
    connection.commit()
    connection.close()