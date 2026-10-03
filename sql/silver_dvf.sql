CREATE TABLE IF NOT EXISTS silver_dvf (
    date_mutation DATE NOT NULL,
    valeur_fonciere NUMERIC NOT NULL,
    code_commune TEXT NOT NULL,
    nom_commune TEXT NOT NULL,
    type_local TEXT,
    surface_reelle_bati NUMERIC,
    prix_m2 NUMERIC,
    source_file TEXT,
    loaded_at TIMESTAMPTZ DEFAULT now()
);