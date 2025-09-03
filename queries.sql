/* QUERY GNERATE */

-- creo indici sulle tabelle principali
CREATE INDEX all_communes_idx
ON all_communes USING GIST(geom);

CREATE INDEX census_idx
ON census_2021 USING GIST(geom);

CREATE INDEX accessibility_idx
ON grid_accessibility_health USING GIST(geom);

-- Creazione della tabella con solo i comuni italiani
CREATE TABLE it_communes AS (
	SELECT *
	FROM "all_communes" c
	WHERE "CNTR_CODE" = 'IT'
);

-- aggiungo colonna per contenere informazioni sulla regione. Codice NUTS2 (rimuovere?)
ALTER TABLE "it_communes"
ADD COLUMN region_id CHAR(4);

-- creo indice sulla tabella
CREATE INDEX it_communes_idx
ON it_communes USING GIST (geom);

-- Q1, calcolo abitanti per comune
select 
    com."COMM_ID",
    com."COMM_NAME", 
    round(SUM(st_area(st_intersection(ce.geom, com.geom))/st_area(ce.geom) * ce."T"))
from 
    census_2021 ce join it_communes com on st_intersects(ce.geom, com.geom)
group by com."COMM_ID", com."COMM_NAME"
order by com."COMM_NAME"

-- query per inserimento valori
WITH pop_calc AS (
    SELECT 
        c."COMM_ID",
        ROUND(SUM(ST_Area(ST_Intersection(g.geom, c.geom)) / 1000000 * g."T")) AS pop
    FROM census_2021 g
    JOIN it_communes c 
      ON ST_Intersects(g.geom, c.geom)
    GROUP BY c."COMM_ID"
)
UPDATE it_communes c
SET pop = p.pop
FROM pop_calc p
WHERE c."COMM_ID" = p."COMM_ID";

-- mostra la griglia che interseca il comune di Roma
SELECT g.fid, g.geom, g."T"
from it_communes c join census_2021 g on ST_Intersects(c.geom, g.geom)
where c."COMM_NAME"= 'Roma'

-- creo la tabella con la popolazione di ogni comune.
-- questa tabella si può non creare e si inserisce la popolazione in it_communes
CREATE TABLE it_comm_with_pop AS (
	select 
	    com."COMM_ID",
	    com."COMM_NAME",
		com.geom,
	    round(SUM(st_area(st_intersection(ce.geom, com.geom))/st_area(ce.geom) * ce."T")) AS pop,
		SUBSTRING(com."NUTS_CODE" FROM 1 FOR 4) AS region_id
	from 
	    census_2021 ce join it_communes com on st_intersects(ce.geom, com.geom)
	group by com."COMM_ID", com."COMM_NAME", com.geom, com."NUTS_CODE"
	order by com."COMM_NAME"
)

/* coloro i comuni sulla base della loro popolazione e della loro densità di popolazione (2 mappe).
genero anche istogramma con distribuzione dei comuni per popolazione.
Il numero di classi è ottenuto con la Sturges's rule, dove n_classi = ceil(log2(n_comuni)) + 1
*/

-- calcolo denità abitativa di ogni comune
alter table it_comm_with_pop
add column density real;

update it_comm_with_pop
set density = pop / (st_area(geom)/1000000);

update it_comm_with_pop
set density = round(density::numeric, 2);

-- crea tabella comuni secondo griglia
create table it_communes_grid as (
	select c."COMM_ID", c."COMM_NAME", c.region_id, g."GRD_ID", st_intersection(c.geom, c.geom) as geom,
		st_area(st_intersection(c.geom, g.geom))/1000000 as partial_pop
	from census_2021 g join it_communes c on st_intersects(g.geom, c.geom)
)

-- aggiungo colonne relative all'accessibilità a cure sanitarie
alter table it_communes_grid
add column health_2020_n1 real,
add column health_2020_n3 real,
add column health_2023_n1 real,
add column health_2023_n3 real;

-- inserisco valori nella tabella comuni con griglia
update it_communes_grid as icg
set health_2020_n1 = gah.health_2020_n1,
	health_2020_n3 = gah.health_2020_n3,
	health_2023_n1 = gah.health_2023_n1,
	health_2023_n3 = gah.health_2023_n3
from grid_accessibility_health gah
where icg."GRD_ID" = gah.grd_id

-- aggiungo colonne a tabella it_communes
alter table it_communes
add column health_2020_n1 real,
add column health_2020_n3 real,
add column health_2023_n1 real,
add column health_2023_n3 real;

-- aggiungo i valori medi di accessibilità nella tabella it_communes
update it_communes as ic
set
	mean_health_2020_n1 = sub.mean_health_2020_n1,
	mean_health_2020_n3 = sub.mean_health_2020_n3,
	mean_health_2023_n1 = sub.mean_health_2023_n1,
	mean_health_2023_n3 = sub.mean_health_2023_n3
from (
	select
		icg."COMM_ID",
		avg(health_2020_n1) as mean_health_2020_n1,
		avg(health_2020_n3) as mean_health_2020_n3,
		avg(health_2023_n1) as mean_health_2023_n1,
		avg(health_2023_n3) as mean_health_2023_n3
	from it_communes_grid icg
	group by icg."COMM_ID"
) as sub
where ic."COMM_ID" = sub."COMM_ID"


-- popolazione per regione
SELECT
	SUBSTRING(c."NUTS_CODE" FROM 1 FOR 4) AS region,
	SUM(pop) as population,
	ST_UNION(c.geom) as geom
FROM it_communes c
GROUP BY SUBSTRING(c."NUTS_CODE" FROM 1 FOR 4)

-- popolazione per provincia
SELECT
	c."NUTS_CODE" AS province, 
	SUM(pop) as population,
	ST_UNION(c.geom) as geom
FROM it_communes c
GROUP BY c."NUTS_CODE"

-- popolazione che vive in ciascuna classe di dimensione del comune
SELECT
    CASE
        WHEN pop < 1000 THEN '< 1.000'
        WHEN pop BETWEEN 1000 AND 4999 THEN '1.000 – 4.999'
        WHEN pop BETWEEN 5000 AND 9999 THEN '5.000 – 9.999'
        WHEN pop BETWEEN 10000 AND 49999 THEN '10.000 – 49.999'
        WHEN pop BETWEEN 50000 AND 99999 THEN '50.000 – 99.999'
        WHEN pop BETWEEN 100000 AND 499999 THEN '100.000 – 499.999'
        ELSE '>= 500.000'
    END AS classe_popolazione,
    COUNT(*) AS num_comuni,
    SUM(pop) AS popolazione_totale,
    ROUND(100.0 * SUM(pop) / (SELECT SUM(pop) FROM it_communes), 2) AS perc_pop_nazionale
FROM it_communes
GROUP BY classe_popolazione
ORDER BY MIN(pop);

-- mostra le classi in intervalli
CASE
        WHEN pop < 1000 THEN '[0, 1k)'
        WHEN pop BETWEEN 1000 AND 4999 THEN '[1k, 5k)'
        WHEN pop BETWEEN 5000 AND 9999 THEN '[5k, 10k)'
        WHEN pop BETWEEN 10000 AND 49999 THEN '[10k, 50k)'
        WHEN pop BETWEEN 50000 AND 99999 THEN '[50k, 100k)'
        WHEN pop BETWEEN 100000 AND 499999 THEN '[100k, 500k)'
        ELSE '[500.000, +inf)'
    END AS classe_popolazione

-- comuni nord italia per popolazione
SELECT
	c."COMM_ID",
	c."COMM_NAME",
	c.geom,
	c.pop
FROM it_communes c
WHERE SUBSTRING(c."NUTS_CODE" FROM 1 FOR 3) IN ('ITC','ITH')
