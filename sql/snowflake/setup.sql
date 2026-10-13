CREATE DATABASE dvf;
CREATE SCHEMA dvf.raw;      -- mirrors "bronze" — landing zone for external data
CREATE SCHEMA dvf.gold;     -- mirrors your Postgres gold layer  

CREATE STORAGE INTEGRATION s3_dvf_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::577060405704:role/snowflake-dvf-role'  -- placeholder, role not created yet
  STORAGE_ALLOWED_LOCATIONS = ('s3://dvf-elt-haitam-2026/gold/');

DESC INTEGRATION s3_dvf_integration;

ALTER STORAGE INTEGRATION s3_dvf_integration
  SET STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::577060405704:role/snowflake-dvf-role';

  CREATE FILE FORMAT dvf.raw.parquet_format
  TYPE = PARQUET;

CREATE STAGE dvf.raw.gold_stage
  STORAGE_INTEGRATION = s3_dvf_integration
  URL = 's3://dvf-elt-haitam-2026/gold/'
  FILE_FORMAT = dvf.raw.parquet_format;

  LIST @dvf.raw.gold_stage;


  CREATE TABLE dvf.gold.commune_yearly_stats (
    code_commune STRING,
    nom_commune STRING,
    year INT,
    nb_transactions INT,
    avg_prix_m2 FLOAT,
    median_prix_m2 FLOAT,
    min_prix_m2 FLOAT,
    max_prix_m2 FLOAT,
    computed_at TIMESTAMP_NTZ
);

COPY INTO dvf.gold.commune_yearly_stats
  FROM @dvf.raw.gold_stage
  FILES = ('commune_yearly_stats_2025.parquet')
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO dvf.gold.commune_yearly_stats
  FROM @dvf.raw.gold_stage/commune_yearly_stats/year=2025/
  FILES = ('commune_yearly_stats_2025.parquet')
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

SELECT count(*) FROM dvf.gold.commune_yearly_stats;

SELECT nom_commune, nb_transactions, avg_prix_m2
FROM dvf.gold.commune_yearly_stats
ORDER BY nb_transactions DESC
LIMIT 5;

SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'DVF.GOLD.COMMUNE_YEARLY_STATS',
  START_TIME => DATEADD(hours, -1, CURRENT_TIMESTAMP())
));