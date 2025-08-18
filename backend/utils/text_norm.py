# backend/utils/text_norm.py
import re
from rapidfuzz import process, fuzz

STOPWORDS = {"fresh", "chopped", "sliced", "diced", "ground", "minced",
             "large", "small", "medium", "organic", "ripe", "skinless",
             "boneless", "cooked", "uncooked", "raw"}

UNIT_WORDS = {"g","gram","grams","kg","ml","l","tbsp","tsp","cup","cups","ounce","ounces","oz","lb","pound","pounds"}

TOKEN_RE = re.compile(r"[A-Za-z]+")

def canonicalize_name(name: str) -> str:
    name = name.lower()
    tokens = TOKEN_RE.findall(name)
    tokens = [t for t in tokens if t not in STOPWORDS and t not in UNIT_WORDS]
    return " ".join(tokens).strip()

def fuzzy_match(query: str, choices: list[str], score_cutoff: int = 88) -> str | None:
    if not choices:
        return None
    match, score, _ = process.extractOne(query, choices, scorer=fuzz.WRatio)
    return match if score >= score_cutoff else None
