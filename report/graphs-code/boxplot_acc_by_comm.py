import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
select c."COMM_ID", c.mean_health_2023_n3 as accessibility
from it_communes c
where SUBSTRING(c."NUTS_CODE" FROM 1 FOR 3) IN ('ITC','ITH')
"""

# Caricamento dati in DataFrame
df = pd.read_sql(query, conn)

# Chiudiamo la connessione
conn.close()

# Creazione boxplot
plt.figure(figsize=(4, 8))
plt.boxplot(df["accessibility"].dropna(), vert=True, patch_artist=True, meanline=True, showmeans=True, meanprops={"color": "red"})

# Etichette e titolo
plt.xlabel("Accessibility time [min]")
#plt.title("Distribution of accessibility times across municipalities")

# Mostra grafico
plt.show()

x = df["accessibility"].dropna()

# Calcolo valori significativi
q1 = x.quantile(0.25)   # Primo quartile (25° percentile)
median = x.median()     # Mediana (50° percentile)
q3 = x.quantile(0.75)   # Terzo quartile (75° percentile)
mean = x.mean()         # Media
iqr = q3 - q1           # Intervallo interquartile

# Estremi "tipici" usati nel boxplot (senza outlier)
lower_whisker = max(x.min(), q1 - 1.5 * iqr)
upper_whisker = min(x.max(), q3 + 1.5 * iqr)

print("Q1 (25%):", q1)
print("Median (50%):", median)
print("Q3 (75%):", q3)
print("IQR:", iqr)
print("Mean:", mean)
print("Lower whisker:", lower_whisker)
print("Upper whisker:", upper_whisker)
