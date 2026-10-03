DELETE FROM silver_dvf WHERE source_file = %(source_file)s;

INSERT INTO silver_dvf
    (date_mutation, valeur_fonciere, code_commune, nom_commune,
     type_local, surface_reelle_bati, prix_m2, source_file)
SELECT DISTINCT ON (date_mutation, code_commune, valeur_fonciere, surface_reelle_bati)
    date_mutation,
    valeur_fonciere,
    code_commune,
    nom_commune,
    type_local,
    surface_reelle_bati,
    CASE
        WHEN surface_reelle_bati > 0 THEN round(valeur_fonciere / surface_reelle_bati, 2)
        ELSE NULL
    END AS prix_m2,
    source_file
FROM bronze_dvf
WHERE source_file = %(source_file)s
  AND valeur_fonciere > 0
  AND date_mutation IS NOT NULL
ORDER BY date_mutation, code_commune, valeur_fonciere, surface_reelle_bati;