DELETE FROM gold_commune_yearly_stats
WHERE year = EXTRACT(YEAR FROM %(as_of_date)s::date)::int;

INSERT INTO gold_commune_yearly_stats
    (code_commune, nom_commune, year, nb_transactions,
     avg_prix_m2, median_prix_m2, min_prix_m2, max_prix_m2)
SELECT
    code_commune,
    nom_commune,
    EXTRACT(YEAR FROM date_mutation)::int AS year,
    count(*) AS nb_transactions,
    round(avg(prix_m2), 2) AS avg_prix_m2,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY prix_m2))::numeric, 2) AS median_prix_m2,
    min(prix_m2) AS min_prix_m2,
    max(prix_m2) AS max_prix_m2
FROM silver_dvf
WHERE prix_m2 IS NOT NULL
  AND EXTRACT(YEAR FROM date_mutation)::int = EXTRACT(YEAR FROM %(as_of_date)s::date)::int
GROUP BY code_commune, nom_commune, EXTRACT(YEAR FROM date_mutation);