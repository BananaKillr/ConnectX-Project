# ==============================================
# File: backend/rag/retriever.py
# ==============================================
import sqlite3
from typing import Dict, Any
from pathlib import Path

from .embeddings import search_ingredients, search_recipes

DB_PATH = str(Path(__file__).resolve().parents[1] / "recipes.sqlite")


def _fetch(conn: sqlite3.Connection, q: str, args: tuple = ()):  # small helper
    cur = conn.cursor()
    cur.execute(q, args)
    return cur.fetchall()


def retrieve(query: str, k_ing: int = 15, k_rec: int = 8) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)

    ing_hits = search_ingredients(query, k_ing)
    rec_hits = search_recipes(query, k_rec)

    ing_ids = [i for i, _ in ing_hits]
    rec_ids = [i for i, _ in rec_hits]

    ings = []
    if ing_ids:
        rows = _fetch(
            conn,
            f"SELECT id, canonical_name, name FROM ingredients WHERE id IN ({','.join('?'*len(ing_ids))})",
            tuple(ing_ids),
        )
        ings = [
            {"id": r[0], "canonical_name": r[1], "name": r[2]}
            for r in rows
        ]

    recs = []
    if rec_ids:
        rows = _fetch(
            conn,
            f"SELECT id, title, COALESCE(text,'') FROM recipes WHERE id IN ({','.join('?'*len(rec_ids))})",
            tuple(rec_ids),
        )
        recs = [{"id": r[0], "title": r[1], "text": r[2]} for r in rows]

    conn.close()
    return {
        "ingredients": ings,
        "recipes": recs,
        "ingredient_hits": ing_hits,
        "recipe_hits": rec_hits,
    }

