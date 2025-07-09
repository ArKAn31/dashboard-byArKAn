import sqlite3

conn = sqlite3.connect("trades.db")
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS trades")

c.execute('''
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        paire TEXT,
        direction TEXT,
        taille_position REAL,
        prix_entree REAL,
        prix_sortie REAL,
        capital REAL
    )
''')

conn.commit()
conn.close()
print("✅ Table 'trades' recréée proprement avec la colonne 'username'.")
