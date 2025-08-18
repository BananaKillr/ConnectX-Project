# backend/utils/nutrition.py
import sqlite3

CAL_ID = 1008  # USDA nutrient id for Energy (kcal)
PROT_ID = 1003
FAT_ID  = 1004
CARB_ID = 1005

def get_db(path="recipes.sqlite"):
    return sqlite3.connect(path)

def nutrition_for_ingredient(conn, canonical_name: str) -> dict | None:
    cur = conn.cursor()
    cur.execute("""
      SELECT i.id
      FROM ingredients i
      WHERE i.canonical_name = ?
      LIMIT 1
    """, (canonical_name,))
    row = cur.fetchone()
    if not row:
        return None
    ingredient_id = row[0]
    cur.execute("""
      SELECT n.name, n.unit_name, inut.amount_per_100g, n.nutrient_id
      FROM ingredient_nutrients inut
      JOIN nutrients n ON n.id = inut.nutrient_id
      WHERE inut.ingredient_id = ?
    """, (ingredient_id,))
    out = {}
    for name, unit, amount, nut_id in cur.fetchall():
        out[nut_id] = {"name": name, "unit": unit, "per_100g": amount}
    return out

def macros_kcal(conn, canonical_name: str) -> dict | None:
    n = nutrition_for_ingredient(conn, canonical_name)
    if not n:
        return None
    def g(nut_id):
        d = n.get(nut_id, {})
        return d.get("per_100g", 0.0)
    return {
        "kcal_per_100g": n.get(CAL_ID, {}).get("per_100g", 0.0),
        "protein_g_per_100g": g(PROT_ID),
        "fat_g_per_100g": g(FAT_ID),
        "carb_g_per_100g": g(CARB_ID),
    }
