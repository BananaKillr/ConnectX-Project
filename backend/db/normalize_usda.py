# backend/db/normalize_usda.py
import os
from pathlib import Path
import pandas as pd
import sqlite3
from backend.utils.text_norm import canonicalize_name

ROOT_DIR = Path(__file__).resolve().parents[1]
USDA_DIR = ROOT_DIR / "data" / "usda"
DB_PATH  = ROOT_DIR / "db" / "recipes.sqlite"

CORE_NUTRIENTS = {1008, 1003, 1004, 1005}  # kcal, protein, fat, carbs

def load_usda_frames():
    food = pd.read_csv(os.path.join(USDA_DIR, "food.csv"))
    food_nutrient = pd.read_csv(os.path.join(USDA_DIR, "food_nutrient.csv"))
    nutrient = pd.read_csv(os.path.join(USDA_DIR, "nutrient.csv"))
    return food, food_nutrient, nutrient


def upsert_ingredients(conn, food_df: pd.DataFrame):
    # Drop rows where description is NaN or empty
    food_df = food_df.dropna(subset=["description"])

    food_df["canonical_name"] = food_df["description"].apply(canonicalize_name)
    cur = conn.cursor()
    for _, r in food_df.iterrows():
        cur.execute("""
          INSERT OR IGNORE INTO ingredients (fdc_id, name, canonical_name, category, data_source)
          VALUES (?, ?, ?, ?, 'USDA')
        """, (int(r.fdc_id), r.description, r.canonical_name, r.data_type))
    conn.commit()


def upsert_nutrients(conn, nutrient_df: pd.DataFrame):
    cur = conn.cursor()
    for _, r in nutrient_df.iterrows():
        cur.execute("""
          INSERT OR IGNORE INTO nutrients (nutrient_id, name, unit_name)
          VALUES (?, ?, ?)
        """, (int(r.id), r.name, r.unit_name))
    conn.commit()

def upsert_ingredient_nutrients(conn, food_nutrient_df: pd.DataFrame):
    cur = conn.cursor()
    fn = food_nutrient_df[food_nutrient_df["nutrient_id"].isin(CORE_NUTRIENTS)]
    cur.execute("SELECT id, fdc_id FROM ingredients")
    mapping = {fdc_id: _id for _id, fdc_id in cur.fetchall()}
    cur.execute("SELECT id, nutrient_id FROM nutrients")
    nutmap = {nutrient_id: _id for _id, nutrient_id in cur.fetchall()}
    rows = []
    for _, r in fn.iterrows():
        ing_id = mapping.get(int(r.fdc_id))
        nut_id = nutmap.get(int(r.nutrient_id))
        if ing_id and nut_id and pd.notnull(r.amount):
            rows.append((ing_id, nut_id, float(r.amount)))
    cur.executemany("""
      INSERT INTO ingredient_nutrients (ingredient_id, nutrient_id, amount_per_100g)
      VALUES (?, ?, ?)
    """, rows)
    conn.commit()

def main():
    food, food_nutrient, nutrient = load_usda_frames()
    conn = sqlite3.connect(DB_PATH)
    upsert_ingredients(conn, food)
    upsert_nutrients(conn, nutrient)
    upsert_ingredient_nutrients(conn, food_nutrient)
    conn.close()
    print("USDA normalization complete.")

if __name__ == "__main__":
    main()
