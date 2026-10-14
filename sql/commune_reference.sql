CREATE TABLE IF NOT EXISTS commune_reference (
    code_commune TEXT PRIMARY KEY,
    nom TEXT,
    population INT,
    code_departement TEXT,
    code_region TEXT,
    fetched_at TIMESTAMPTZ DEFAULT now()
);