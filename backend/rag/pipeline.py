# backend/rag/pipeline.py
from typing import List, Optional
from backend.rag.embeddings import search_recipes, search_ingredients
from backend.rag.context import build_context_for_recipes
from google.genai import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize the GenAI client
client = Client(api_key=GOOGLE_API_KEY)


def plan_recipe(
    user_query: str,
    calories: Optional[int] = None,
    diet: Optional[str] = None,
    allergens: Optional[List[str]] = None,
    k_ing: int = 15,
    k_rec: int = 8,
):
    allergens = allergens or []

    # Step 1: Search for relevant recipes
    rec_results = search_recipes(user_query, k=k_rec)
    recipe_ids = [r[0] for r in rec_results]

    # Step 2: If recipe search sparse, supplement with ingredient search
    if len(recipe_ids) < k_rec:
        ing_results = search_ingredients(user_query, k=k_ing)
        # Add ingredient-matched recipes without duplicates
        for rid, _ in ing_results:
            if rid not in recipe_ids:
                recipe_ids.append(rid)
        print("Ingredient search supplemented missing recipes.")
    else:
        ing_results = []

    # Debug prints
    print("Recipe IDs from recipe search:", [r[0] for r in rec_results])
    print("Recipe IDs from ingredient search:", [r[0] for r in ing_results])
    print("Combined recipe IDs:", recipe_ids)

    # Step 3: Build context
    context_text = build_context_for_recipes(recipe_ids)
    print("Context text being sent to Gemini:\n", context_text)

    if not context_text:
        context_text = "(No relevant recipes found in database. Use general knowledge to suggest a recipe.)"

    # Step 4: Build prompt
    prompt = f"""
    You are a helpful AI chef assistant.

    User asked: {user_query}

    Constraints:
    - Calories: {calories or 'any'}
    - Diet: {diet or 'any'}
    - Allergens to avoid: {', '.join(allergens) if allergens else 'none'}

    Use the following recipes to suggest a suitable recipe:
    {context_text}

    Respond with a complete recipe, including:
    - Title of the dish
    - Ingredients with exact amounts (grams, cups, tablespoons, etc.)
    - Step-by-step method with detailed cooking times and temperatures
    - Serving size and calorie estimate
    
    Do not include any extra explanations or notes
    """

    # Step 5: Generate content
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt]
    )


    # Step 6: Return results
    return {
        "retrieved_recipe_ids": recipe_ids,
        "context": context_text,
        "generated_text": response.text,
    }
