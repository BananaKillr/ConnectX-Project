from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from backend.rag.pipeline import plan_recipe
from backend.rag.embeddings import build_ingredient_index, build_recipe_index

app = FastAPI(title="Recipe RAG API (Gemini)")


class GenerateRequest(BaseModel):
    query: str
    calories: Optional[int] = None
    diet: Optional[str] = None
    allergens: Optional[List[str]] = []
    k_ing: int = 15
    k_rec: int = 8


@app.post("/generate_recipe")
def generate_recipe_ep(body: GenerateRequest):
    out = plan_recipe(
        user_query=body.query,
        calories=body.calories,
        diet=body.diet,
        allergens=body.allergens or [],
        k_ing=body.k_ing,
        k_rec=body.k_rec,
    )
    return out


@app.post("/rebuild_indices")
def rebuild_indices():
    build_ingredient_index()
    build_recipe_index()
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}