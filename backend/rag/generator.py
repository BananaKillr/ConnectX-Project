# ==============================================
# File: backend/gemini/generator.py
# ==============================================
import os
import google.generativeai as genai

MODEL = "gemini-1.5-pro"  # you can use -flash for speed


def _cfg():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    genai.configure(api_key=api_key)


def generate_recipe(context: dict, constraints: dict) -> dict:
    """Ask Gemini to return a structured JSON recipe."""
    _cfg()
    system = (
        "You are a meticulous culinary assistant. Generate one recipe that strictly respects the constraints. "
        "Use only candidate ingredients if provided. Return pure JSON conforming to the schema."
    )

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "servings": {"type": "integer"},
            "ingredients": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"}
                    },
                    "required": ["name", "quantity", "unit"]
                }
            },
            "steps": {"type": "array", "items": {"type": "string"}},
            "nutrition": {
                "type": "object",
                "properties": {
                    "calories": {"type": "number"},
                    "protein_g": {"type": "number"},
                    "fat_g": {"type": "number"},
                    "carbs_g": {"type": "number"}
                },
                "required": ["calories", "protein_g", "fat_g", "carbs_g"]
            }
        },
        "required": ["title", "servings", "ingredients", "steps", "nutrition"]
    }

    # Newer SDKs allow response_mime_type. If not supported in your version, fall back to text and json.loads.
    model = genai.GenerativeModel(model_name=MODEL)

    prompt = (
        f"CONSTRAINTS:\n{constraints}\n\n"
        f"CANDIDATE_CONTEXT (for grounding):\n{context}\n\n"
        "Return only valid JSON (no markdown fences)."
    )

    resp = model.generate_content(prompt, generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.6,
    })

    try:
        return resp.parsed if hasattr(resp, "parsed") and resp.parsed else __import__("json").loads(resp.text)
    except Exception:
        return {"error": "Failed to parse JSON from model", "raw": getattr(resp, "text", None)}

