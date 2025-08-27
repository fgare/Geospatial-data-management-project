import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Connessione al database
conn = psycopg2.connect(
    dbname="GDM-proj",
    user="postgres",
    password="scooter",
    host="localhost",
    port="5432"
)

# Query
query = """
SELECT
	c."COMM_ID",
	c."COMM_NAME",
	c.geom,
	c.mean_health_2023_n1 as accessibility,
	case
		when c.mean_health_2023_n1 < 15 then 1
		when c.mean_health_2023_n1 between 15 and 30 then 2
		when c.mean_health_2023_n1 between 30 and 45 then 3
		when c.mean_health_2023_n1 > 45 then 4
	end as classe
FROM it_communes c
WHERE SUBSTRING(c."NUTS_CODE" FROM 1 FOR 3) IN ('ITC','ITH')
"""

# Carico i dati in un DataFrame
df = pd.read_sql(query, conn)

# Chiudo la connessione
conn.close()

# Conta il numero di comuni per classe
counts = df['classe'].value_counts().sort_index()

# Istogramma
bars = plt.bar(counts.index, counts.values)
plt.xlabel("Class of accessibility")
plt.ylabel("No. of municipalities")
#plt.title("Class [min]")
plt.xticks([1,2,3,4])  # etichette fisse

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,   # posizione x centrata
        height,                              # altezza della barra
        str(height),                         # testo (il valore)
        ha='center', va='bottom'             # centrato orizzontalmente, sopra la barra
    )

plt.show()
