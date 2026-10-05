CREATE TABLE IF NOT EXISTS gold_commune_yearly_stats (
    code_commune TEXT NOT NULL,
    nom_commune TEXT NOT NULL,
    year INT NOT NULL,
    nb_transactions INT NOT NULL,
    avg_prix_m2 NUMERIC,
    median_prix_m2 NUMERIC,
    min_prix_m2 NUMERIC,
    max_prix_m2 NUMERIC,
    computed_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (code_commune, year)
);