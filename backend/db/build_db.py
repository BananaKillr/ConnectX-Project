# db/build_db.py
import sqlite3
from pathlib import Path
from normalize_usda import main as build_usda
from normalize_recipenlg import main as build_nlg

DB_PATH = "recipes.sqlite"
SCHEMA  = r"C:\Users\youss\Desktop\Connect X\AAAAAAAAHHHH\pythonProject\backend\db\schema.sql"

def main():
    if not Path(DB_PATH).exists():
        conn = sqlite3.connect(DB_PATH)
        with open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()
        print("Created SQLite + schema.")
    else:
        print("Using existing SQLite.")

    build_usda()
    build_nlg()
    print("DB build complete.")

if __name__ == "__main__":
    main()
