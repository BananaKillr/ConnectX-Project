# backend/db/normalize_recipenlg.py
import os
from pathlib import Path

import pandas as pd
import sqlite3
from backend.utils.text_norm import canonicalize_name

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH  = ROOT_DIR / "db" / "recipes.sqlite"

NLG_PATH = ROOT_DIR / "data" / "recipenlg" / "full_dataset.csv"

C_TITLE   = "title"
C_INGR    = "ingredients"
C_METHOD  = "directions"
C_TAGS    = "ner"  # maps directly to schema `tags` column

def split_ingredients(raw) -> list[str]:
    if pd.isna(raw):
        return []
    txt = str(raw).strip().strip("[]")
    parts = [p.strip(" '\"") for p in txt.split(",") if p.strip()]
    if len(parts) <= 1:
        parts = [s.strip() for s in txt.replace("\n", ";").split(";") if s.strip()]
    return parts

def main():
    df = pd.read_csv(NLG_PATH).fillna("")
    df = df.sample(n=25000, random_state=42)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for idx, r in df.iterrows():
        title = r.get(C_TITLE, "").strip() or "Untitled"
        text  = str(r.get(C_METHOD, "")).strip()
        tags  = str(r.get(C_TAGS, "")).strip()

        cur.execute("""
          INSERT INTO recipes (source_id, title, text, tags)
          VALUES (?, ?, ?, ?)
        """, (str(idx), title, text, tags))
        recipe_id = cur.lastrowid

        ingredients = split_ingredients(r.get(C_INGR, ""))
        for raw_ing in ingredients:
            can = canonicalize_name(raw_ing)
            cur.execute("""
              INSERT INTO recipe_ingredients (recipe_id, raw_ingredient, canonical_ingredient)
              VALUES (?, ?, ?)
            """, (recipe_id, raw_ing, can))

    conn.commit()
    conn.close()
    print("RecipeNLG normalization (25000 recipes) complete.")

if __name__ == "__main__":
    main()
