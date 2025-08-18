-- backend/db/schema.sql
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS ingredients (
  id INTEGER PRIMARY KEY,
  fdc_id INTEGER UNIQUE,
  name TEXT NOT NULL,
  canonical_name TEXT NOT NULL,   -- normalized name for matching
  category TEXT,
  data_source TEXT DEFAULT 'USDA' -- 'USDA' or other
);

CREATE TABLE IF NOT EXISTS nutrients (
  id INTEGER PRIMARY KEY,
  nutrient_id INTEGER UNIQUE,     -- USDA nutrient.id or an internal code
  name TEXT NOT NULL,
  unit_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredient_nutrients (
  id INTEGER PRIMARY KEY,
  ingredient_id INTEGER NOT NULL,
  nutrient_id INTEGER NOT NULL,
  amount_per_100g REAL NOT NULL,  -- normalized to per 100g
  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
  FOREIGN KEY (nutrient_id) REFERENCES nutrients(id)
);

CREATE TABLE IF NOT EXISTS recipes (
  id INTEGER PRIMARY KEY,
  source_id TEXT,                 -- id in RecipeNLG
  title TEXT NOT NULL,
  text TEXT,                      -- full text / instructions
  meal_tags TEXT,                 -- comma-separated or JSON string
  diet_tags TEXT                  -- comma-separated or JSON string
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
  id INTEGER PRIMARY KEY,
  recipe_id INTEGER NOT NULL,
  raw_ingredient TEXT NOT NULL,
  canonical_ingredient TEXT,      -- normalized name to match USDA
  quantity FLOAT,                 -- numeric amount if parsed (optional)
  unit TEXT,                      -- unit if parsed (optional)
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);
