import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib

# Connexion à la base users
conn_users = sqlite3.connect("users.db", check_same_thread=False)
cur_users = conn_users.cursor()

# Création table users si inexistante
cur_users.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')
conn_users.commit()

# Connexion à la base trades
conn_trades = sqlite3.connect("trades.db", check_same_thread=False)
cur_trades = conn_trades.cursor()

# Création table trades si inexistante
cur_trades.execute('''
CREATE TABLE IF NOT EXISTS trades (
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
conn_trades.commit()

# Fonction pour hasher les mots de passe (SHA256 simple)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Fonction pour vérifier login
def login(username, password):
    hashed = hash_password(password)
    cur_users.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed))
    return cur_users.fetchone() is not None

# Fonction pour enregistrer un nouvel utilisateur
def register(username, password):
    hashed = hash_password(password)
    try:
        cur_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn_users.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Config page
st.set_page_config(page_title="Dashboard Trading Pro", layout="wide")
st.title("📊 Dashboard Trading Pro")

# Initialisation session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# Si pas connecté, proposer inscription ou login
if not st.session_state.logged_in:
    st.subheader("🔐 Connexion / Inscription")

    tab1, tab2 = st.tabs(["Se connecter", "S'inscrire"])

    with tab1:
        with st.form("login_form"):
            username_login = st.text_input("Nom d'utilisateur")
            password_login = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            if submit_login:
                if login(username_login, password_login):
                    st.session_state.logged_in = True
                    st.session_state.username = username_login
                    st.experimental_rerun()  # rerun immédiat, pas de message ici
                else:
                    st.error("❌ Identifiants incorrects.")

    with tab2:
        with st.form("register_form"):
            username_reg = st.text_input("Nom d'utilisateur", key="reg_user")
            password_reg = st.text_input("Mot de passe", type="password", key="reg_pass")
            password_confirm = st.text_input("Confirmez le mot de passe", type="password", key="reg_pass_confirm")
            submit_reg = st.form_submit_button("S'inscrire")
            if submit_reg:
                if password_reg != password_confirm:
                    st.error("❌ Les mots de passe ne correspondent pas.")
                elif len(password_reg) < 4:
                    st.error("❌ Le mot de passe doit contenir au moins 4 caractères.")
                elif len(username_reg.strip()) == 0:
                    st.error("❌ Le nom d'utilisateur ne peut pas être vide.")
                else:
                    success = register(username_reg.strip(), password_reg)
                    if success:
                        st.success("✅ Inscription réussie ! Vous pouvez maintenant vous connecter.")
                    else:
                        st.error("❌ Ce nom d'utilisateur est déjà pris.")

else:
    st.success(f"👋 Bienvenue {st.session_state.username}")
    st.header("💼 Nouveau Trade")

    # Liste étendue de paires Forex + Crypto
    paires = [
        "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "BTC/USDT",
        "ETH/USDT", "XAU/USD", "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY",
        "LTC/USDT", "ADA/USDT", "DOGE/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT"
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        paire = st.selectbox("Paire tradée", options=paires)
        direction = st.radio("Direction", options=["BUY", "SELL"])
    with col2:
        capital = st.number_input("💰 Capital total (€)", min_value=0.0, value=10000.0, step=100.0)
        taille_pct = st.slider("📏 Taille de la position (%)", min_value=0.01, max_value=100.0, value=1.0)
    with col3:
        prix_entree = st.number_input("🎯 Prix d'entrée", format="%.5f")
        prix_sortie = st.number_input("🎯 Prix de sortie", format="%.5f")

    if st.button("✅ Enregistrer le trade"):
        if capital <= 0:
            st.error("Le capital doit être supérieur à 0.")
        elif taille_pct <= 0:
            st.error("La taille de la position doit être supérieure à 0%.")
        elif prix_entree <= 0 or prix_sortie <= 0:
            st.error("Les prix doivent être supérieurs à 0.")
        else:
            cur_trades.execute('''
                INSERT INTO trades (username, paire, direction, taille_position, prix_entree, prix_sortie, capital)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                st.session_state.username,
                paire,
                direction,
                taille_pct,
                prix_entree,
                prix_sortie,
                capital
            ))
            conn_trades.commit()
            st.success("💾 Trade enregistré avec succès !")

    st.divider()

    st.subheader("📈 Historique de vos trades")
    cur_trades.execute("SELECT * FROM trades WHERE username = ?", (st.session_state.username,))
    rows = cur_trades.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Utilisateur", "Paire", "Direction", "Taille %", "Prix entrée", "Prix sortie", "Capital"])
        df["Gain/Perte (€)"] = df.apply(lambda row: 
            ((row["Prix sortie"] - row["Prix entrée"]) if row["Direction"] == "BUY"
             else (row["Prix entrée"] - row["Prix sortie"]))
             * row["Capital"] * (row["Taille %"] / 100), axis=1
        )
        df_display = df[["ID", "Paire", "Direction", "Taille %", "Prix entrée", "Prix sortie", "Capital", "Gain/Perte (€)"]]

        def highlight_direction(row):
            color = 'background-color: #d4f8d4' if row.Direction == 'BUY' else 'background-color: #f8d4d4'
            return [color]*len(row)

        st.dataframe(df_display.style.apply(highlight_direction, axis=1), use_container_width=True)

        df['Cumul Gain/Perte (€)'] = df["Gain/Perte (€)"].cumsum()
        fig = px.line(df, x="ID", y="Cumul Gain/Perte (€)", title="Évolution cumulative des gains/pertes")
        st.plotly_chart(fig, use_container_width=True)

        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Exporter l'historique CSV", data=csv, file_name="historique_trades.csv", mime="text/csv")

    else:
        st.info("Aucun trade enregistré pour l’instant.")

    if st.button("🚪 Se déconnecter"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()





