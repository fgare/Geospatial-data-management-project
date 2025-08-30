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
    CASE
        WHEN pop < 1000 THEN '[0, 1k)'
        WHEN pop BETWEEN 1000 AND 4999 THEN '[1k, 5k)'
        WHEN pop BETWEEN 5000 AND 9999 THEN '[5k, 10k)'
        WHEN pop BETWEEN 10000 AND 49999 THEN '[10k, 50k)'
        WHEN pop BETWEEN 50000 AND 99999 THEN '[50k, 100k)'
        WHEN pop BETWEEN 100000 AND 499999 THEN '[100k, 500k)'
        ELSE '[500.000, +inf)'
    END AS classe_popolazione,
    COUNT(*) AS num_comuni,
    SUM(pop) AS popolazione_totale,
    ROUND(100.0 * SUM(pop) / (SELECT SUM(pop) FROM it_communes), 2) AS perc_pop_nazionale
FROM it_communes
GROUP BY classe_popolazione
ORDER BY MIN(pop);
"""

df = pd.read_sql(query, conn)
conn.close()

# Ordina le classi per popolazione totale decrescente
df = df.sort_values("popolazione_totale", ascending=False).reset_index(drop=True)

# Calcola cumulata
df["cumulata"] = df["popolazione_totale"].cumsum() / df["popolazione_totale"].sum() * 100

df["pop_milioni"] = df["popolazione_totale"] / 10**6
# Grafico Pareto
fig, ax1 = plt.subplots(figsize=(10, 6))

# Barre (popolazione totale)
ax1.bar(df["classe_popolazione"], df["pop_milioni"], color="skyblue", width=0.95)
ax1.set_ylabel("Total population [10e+6]")
ax1.tick_params(axis="x", rotation=0)

# Linea cumulata (secondo asse Y)
ax2 = ax1.twinx()
ax2.plot(df["classe_popolazione"], df["cumulata"], color="red", marker="o", linewidth=2)
ax2.set_ylabel("Cumulative % of population")

# Titolo
#plt.title("Grafico di Pareto – Distribuzione della popolazione per classe di comune")

# Mostra
plt.tight_layout()
plt.show()
