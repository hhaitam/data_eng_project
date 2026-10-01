CREATE TABLE IF NOT EXISTS bronze_dvf (
    date_mutation DATE,
    valeur_fonciere NUMERIC,
    code_commune TEXT,
    nom_commune TEXT,
    type_local TEXT,
    surface_reelle_bati NUMERIC,
    source_file TEXT,
    loaded_at TIMESTAMPTZ DEFAULT now()
);