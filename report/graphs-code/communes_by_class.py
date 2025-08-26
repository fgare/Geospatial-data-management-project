import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Connessione al DB
conn = psycopg2.connect(
    dbname="GDM-proj",
    user="postgres",
    password="scooter",
    host="localhost",
    port="5432"
)

# Scrivi direttamente la query
query = """
SELECT
    CASE
        WHEN pop < 1000 THEN '[0,1k)'
        WHEN pop BETWEEN 1000 AND 4999 THEN '[1k,5k)'
        WHEN pop BETWEEN 5000 AND 9999 THEN '[5k,10k)'
        WHEN pop BETWEEN 10000 AND 49999 THEN '[10k,50k)'
        WHEN pop BETWEEN 50000 AND 99999 THEN '[15k,100k)'
        WHEN pop BETWEEN 100000 AND 499999 THEN '[100k,500k)'
        ELSE '[500.000,+inf)'
    END AS classe_popolazione,
    COUNT(*) AS num_comuni,
    SUM(pop) AS popolazione_totale,
    ROUND(100.0 * SUM(pop) / (SELECT SUM(pop) FROM it_communes), 2) AS perc_pop_nazionale
FROM it_communes
GROUP BY classe_popolazione
ORDER BY MIN(pop);

"""

# Carica i dati in un DataFrame pandas
df = pd.read_sql_query(query, conn)

# Chiudi la connessione
conn.close()

df['pop_cumulativa_milioni'] = df['popolazione_totale'].cumsum() / 1_000_000

fig, ax1 = plt.subplots(figsize=(10,6))
ax1.bar(df["classe_popolazione"], df["num_comuni"], color="skyblue", label="No. of municipalities")
ax1.set_xlabel("Class")
ax1.set_ylabel("No. of municipalities")
ax1.tick_params(axis='x')

# Linea popolazione totale sulla stessa figura
ax2 = ax1.twinx()
ax2.plot(df["classe_popolazione"], df["popolazione_totale"]/10**6, color="orange", marker="o", label="Total population")
ax2.plot(df["classe_popolazione"], df["pop_cumulativa_milioni"], color="red", marker="s", linestyle="--", label="Cumulative population")
ax2.set_ylabel("Population [E+6]")

# Legenda combinata
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="center right")

#plt.title("Distribuzione dei comuni italiani per classe di popolazione")
plt.tight_layout()
plt.show()