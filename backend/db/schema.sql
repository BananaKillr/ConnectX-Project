PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS ingredients (
  id INTEGER PRIMARY KEY,
  fdc_id INTEGER UNIQUE,
  name TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  category TEXT,
  data_source TEXT DEFAULT 'USDA'
);

CREATE TABLE IF NOT EXISTS nutrients (
  id INTEGER PRIMARY KEY,
  nutrient_id INTEGER UNIQUE,
  name TEXT NOT NULL,
  unit_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredient_nutrients (
  id INTEGER PRIMARY KEY,
  ingredient_id INTEGER NOT NULL,
  nutrient_id INTEGER NOT NULL,
  amount_per_100g REAL NOT NULL,
  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
  FOREIGN KEY (nutrient_id) REFERENCES nutrients(id)
);

-- Cleaned-up recipes table
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    text TEXT,
    tags TEXT,
    source_id TEXT,  -- add this if normalize_recipenlg expects it
    link TEXT,
    source TEXT,
    ner TEXT
);


CREATE TABLE IF NOT EXISTS recipe_ingredients (
  id INTEGER PRIMARY KEY,
  recipe_id INTEGER NOT NULL,
  raw_ingredient TEXT NOT NULL,
  canonical_ingredient TEXT,
  quantity FLOAT,
  unit TEXT,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);
