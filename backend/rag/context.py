# backend/rag/context.py
import sqlite3
from typing import List
from .embeddings import DB_PATH


def build_context_for_recipes(recipe_ids: List[int]) -> str:
    if not recipe_ids:
        return ""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Use 'tags' instead of 'meal_tags'
    query = f"""
        SELECT title, COALESCE(text, ''), COALESCE(tags, '')
        FROM recipes
        WHERE id IN ({','.join('?' * len(recipe_ids))})
    """
    cursor.execute(query, recipe_ids)
    rows = cursor.fetchall()
    conn.close()

    parts = []
    for title, text, tags in rows:
        part = (
            f"Title: {title}\n"
            f"Tags: {tags}\n"
            f"Method: {text}\n"
        )
        parts.append(part)

    return "\n---\n".join(parts)
