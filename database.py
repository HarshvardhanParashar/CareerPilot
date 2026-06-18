import sqlite3
import os

DB_PATH = os.path.join("database", "careerpilot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_connection()

    with open("sql/schema.sql", "r") as file:
        conn.executescript(file.read())

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database created successfully!")