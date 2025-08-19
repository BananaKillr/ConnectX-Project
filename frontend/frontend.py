import streamlit as st
import requests
import re

# ==== CONFIG ====
API_BASE = "http://localhost:8000"  # Your FastAPI host
GENERATE_ENDPOINT = f"{API_BASE}/generate_recipe"

st.set_page_config(page_title="Nutrition & Recipe Guide", page_icon="🍎", layout="wide")

# ==== SESSION STATE ====
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==== TITLE ====
st.title("🍎 Nutrition & Recipe Guide")
st.markdown("""
Ask me about:
- 🥗 Meal plans for your dietary needs  
- 🍲 Cooking recipes (step-by-step)  
- 🍌 Nutritional guidance for health conditions  
""")

# ==== USER INPUTS ====
with st.sidebar:
    st.header("Your Preferences")
    calories = st.number_input("Calories (max)", min_value=0, step=50)
    diet = st.text_input("Diet type (e.g., vegan, keto, vegetarian)")
    allergens = st.text_input("Allergens to avoid (comma-separated)")

# ==== CHAT DISPLAY ====
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

# ==== CHAT INPUT ====
if prompt := st.chat_input("What meal or recipe would you like guidance on?"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Parse allergens into a list
    allergen_list = [a.strip() for a in allergens.split(",") if a.strip()]

    # Call API
    try:
        payload = {
            "query": prompt,
            "calories": calories if calories > 0 else None,
            "diet": diet if diet else None,
            "allergens": allergen_list,
            "k_ing": 15,
            "k_rec": 8
        }
        res = requests.post(GENERATE_ENDPOINT, json=payload)
        if res.status_code == 200:
            bot_reply = res.json()
            bot_text = bot_reply.get("generated_text", str(bot_reply))
        else:
            bot_text = f"⚠ Error: {res.status_code} {res.text}"
    except Exception as e:
        bot_text = f"⚠ Exception: {e}"

    # Append bot reply
    st.session_state.messages.append({"role": "assistant", "content": bot_text})
    st.chat_message("assistant").markdown(bot_text)
