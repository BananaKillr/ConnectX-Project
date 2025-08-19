# backend/rag/embeddings.py

import os
import sqlite3
import numpy as np
import google.generativeai as genai
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

ROOT_DIR = Path(__file__).resolve().parent.parent  # project root
DB_PATH = ROOT_DIR / "db" / "recipes.sqlite"
BATCH_SIZE = 250

# -------------------------------------------------------------------
# DB connection
# -------------------------------------------------------------------
def _get_conn():
    return sqlite3.connect(DB_PATH)

# -------------------------------------------------------------------
# Embedding helper
# -------------------------------------------------------------------
def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed one or more texts using Gemini embeddings.
    Returns a NumPy array of shape (n, dim).
    """
    model = "models/embedding-001"
    if isinstance(texts, str):
        texts = [texts]

    response = genai.embed_content(model=model, content=texts)

    # Single string -> dict with 'embedding'
    if isinstance(response, dict) and "embedding" in response:
        return np.array(response["embedding"], dtype=np.float32)

    # Batch -> list of embeddings
    if isinstance(response, list):
        embs = []
        for item in response:
            if isinstance(item, dict) and "embedding" in item:
                embs.append(item["embedding"])
            elif isinstance(item, list):
                embs.append(item)
            else:
                raise RuntimeError(f"Unexpected embedding format: {item}")
        return np.array(embs, dtype=np.float32)

    raise RuntimeError(f"Unexpected response from Gemini: {response}")

# -------------------------------------------------------------------
# Ingredient index
# -------------------------------------------------------------------
def build_ingredient_index():
    conn = _get_conn()
    cur = conn.cursor()

    # Create embeddings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_embeddings (
            ingredient_id INTEGER PRIMARY KEY,
            embedding BLOB,
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)
    conn.commit()

    # Fetch all ingredients
    cur.execute("SELECT id, canonical_name FROM ingredients")
    rows = cur.fetchall()
    total = len(rows)
    if total == 0:
        print("No ingredients found in DB")
        return

    print(f"Rebuilding ingredient index for {total} ingredients...")

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        texts = []
        ids = []
        for ing_id, cname in batch:
            if cname:
                texts.append(cname)
                ids.append(ing_id)

        if not texts:
            continue

        try:
            embs = embed_texts(texts)
        except Exception as e:
            print(f"Embedding failed on batch {i}-{i+len(batch)}: {e}")
            continue

        for ing_id, emb in zip(ids, embs):
            cur.execute("""
                INSERT OR REPLACE INTO ingredient_embeddings (ingredient_id, embedding)
                VALUES (?, ?)
            """, (ing_id, emb.tobytes()))

        conn.commit()
        print(f"Processed {i + len(batch)} / {total} ingredients")

    conn.close()
    print("Ingredient index rebuild complete!")

# -------------------------------------------------------------------
# Recipe index
# -------------------------------------------------------------------
def build_recipe_index():
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_embeddings (
            recipe_id INTEGER PRIMARY KEY,
            embedding BLOB,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
    """)
    conn.commit()

    # Only include useful columns
    cur.execute("SELECT id, title, text FROM recipes")
    rows = cur.fetchall()
    total = len(rows)
    if total == 0:
        print("No recipes found in DB")
        return

    print(f"Rebuilding recipe index for {total} recipes...")

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        texts = []
        ids = []
        for recipe_id, title, text in batch:
            parts = []
            if title:
                parts.append(title)
            if text:
                parts.append(text)
            full_text = "\n".join(parts).strip()
            if full_text:
                texts.append(full_text)
                ids.append(recipe_id)

        if not texts:
            continue

        try:
            embs = embed_texts(texts)
        except Exception as e:
            print(f"Embedding failed on batch {i}-{i+len(batch)}: {e}")
            continue

        for recipe_id, emb in zip(ids, embs):
            cur.execute("""
                INSERT OR REPLACE INTO recipe_embeddings (recipe_id, embedding)
                VALUES (?, ?)
            """, (recipe_id, emb.tobytes()))

        conn.commit()
        print(f"Processed {i + len(batch)} / {total} recipes")

    conn.close()
    print("Recipe index rebuild complete!")


def search_recipes(query: str, k: int = 10):
    """Return top-k recipes by embedding similarity (with names instead of IDs)."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.title, r.text, e.embedding
        FROM recipe_embeddings e
        JOIN recipes r ON r.id = e.recipe_id
    """)
    rows = cur.fetchall()
    conn.close()

    # Convert query to embedding
    q_emb = embed_texts(query).astype(np.float32)

    # Compute cosine similarity
    results = []
    for recipe_id, title, text, emb_blob in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        sim = np.dot(q_emb, emb) / (np.linalg.norm(q_emb) * np.linalg.norm(emb))
        results.append((title, text, sim))

    # Sort & return top-k (title + maybe snippet)
    return sorted(results, key=lambda x: x[2], reverse=True)[:k]


def search_ingredients(query: str, k: int = 10):
    # similar approach if you create an ingredient embedding table
    ...


# -------------------------------------------------------------------
# Main entry
# -------------------------------------------------------------------
def main():
    #build_ingredient_index()
    build_recipe_index()

if __name__ == "__main__":
    main()
