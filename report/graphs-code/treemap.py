import pandas as pd
import matplotlib.pyplot as plt
import squarify  # pip install squarify
import psycopg2

# Connessione al database
conn = psycopg2.connect(
    dbname="GDM-proj",
    user="postgres",
    password="scooter",
    host="localhost",
    port="5432"
)

query = """
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
    SUM(pop) AS popolazione_totale
FROM it_communes c
GROUP BY c.pop
ORDER BY
    CASE
        WHEN pop < 1000 THEN 1
        WHEN pop BETWEEN 1000 AND 4999 THEN 2
        WHEN pop BETWEEN 5000 AND 9999 THEN 3
        WHEN pop BETWEEN 10000 AND 49999 THEN 4
        WHEN pop BETWEEN 50000 AND 99999 THEN 5
        WHEN pop BETWEEN 100000 AND 499999 THEN 6
        ELSE 7
    END;
"""

df = pd.read_sql_query(query, conn)
conn.close()

# Imposta etichette per il treemap
labels = [f"{row['classe_popolazione']}\n{row['num_comuni']} comuni\n{row['popolazione_totale']/1_000_000:.1f}M abitanti"
          for i, row in df.iterrows()]

# Colori proporzionali alla popolazione
colors = plt.cm.viridis(df['popolazione_totale'] / df['popolazione_totale'].max())

plt.figure(figsize=(12,6))
squarify.plot(sizes=df['num_comuni'], label=labels, color=colors, alpha=0.8, edgecolor="white", linewidth=2)
plt.axis('off')
plt.title("Treemap dei comuni italiani per classe di popolazione\nArea proporzionale al numero di comuni, colore proporzionale alla popolazione totale")
plt.show()
