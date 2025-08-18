# backend/db/normalize_recipenlg.py
import os
import pandas as pd
import sqlite3
from backend.utils.text_norm import canonicalize_name

NLG_PATH = r"C:\Users\youss\Desktop\Connect X\AAAAAAAAHHHH\pythonProject\backend\data\recipenlg\full_dataset.csv"
DB_PATH  = "recipes.sqlite"

# Adjust these column names if your CSV differs
C_TITLE   = "title"
C_INGR    = "ingredients"      # stringified list or text
C_METHOD  = "directions"       # instructions / method
C_TAGS    = "ner"              # or "tags" if present

def split_ingredients(raw) -> list[str]:
    if pd.isna(raw):
        return []
    # Many RecipeNLG builds store it like: "['1 cup quinoa','2 tomatoes',...]"
    txt = str(raw).strip()
    txt = txt.strip("[]")
    parts = [p.strip(" '\"") for p in txt.split(",") if p.strip()]
    # Fallback: semicolon or newline
    if len(parts) <= 1:
        parts = [s.strip() for s in txt.replace("\n", ";").split(";") if s.strip()]
    return parts

def parse_tags(raw) -> str:
    if pd.isna(raw):
        return ""
    return ",".join(sorted({t.strip().lower() for t in str(raw).split(",") if t.strip()}))

def main():
    df = pd.read_csv(NLG_PATH)
    df = df.fillna("")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for _, r in df.iterrows():
        title = r.get(C_TITLE, "").strip() or "Untitled"
        text  = str(r.get(C_METHOD, "")).strip()
        meal_tags = ""  # optional: derive from title/text
        diet_tags = ""  # optional: derive with a classifier later
        cur.execute("""
          INSERT INTO recipes (source_id, title, text, meal_tags, diet_tags)
          VALUES (?, ?, ?, ?, ?)
        """, (str(_), title, text, meal_tags, diet_tags))
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
    print("RecipeNLG normalization complete.")

if __name__ == "__main__":
    main()
