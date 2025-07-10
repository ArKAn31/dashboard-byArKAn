-import sqlite3

# Connexion à la base de données
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Création de la table des utilisateurs
c.execute("DROP TABLE IF EXISTS users")
c.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
conn.commit()
conn.close()

# Connexion à la base de données des trades
conn = sqlite3.connect("trades.db")
c = conn.cursor()

# Création de la table des trades
c.execute("DROP TABLE IF EXISTS trades")
c.execute("""
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        paire TEXT NOT NULL,
        direction TEXT NOT NULL,
        taille_position REAL NOT NULL,
        prix_entree REAL NOT NULL,
        prix_sortie REAL NOT NULL,
        capital REAL NOT NULL
    )
""")
conn.commit()
conn.close()

print("✅ Bases de données 'users.db' et 'trades.db' initialisées avec succès.")
