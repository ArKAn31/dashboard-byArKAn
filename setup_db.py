import sqlite3

conn = sqlite3.connect("trades.db")
c = conn.cursor()

# Supprime et recrée la table
c.execute("DROP TABLE IF EXISTS trades")

c.execute("""
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paire TEXT NOT NULL,
        ordre TEXT NOT NULL,
        taille_position REAL NOT NULL,
        prix_entree REAL NOT NULL,
        prix_sortie REAL NOT NULL,
        capital REAL NOT NULL
    )
""")

conn.commit()
conn.close()
print("Base de données des trades réinitialisée avec succès.")
