import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import os

# Forcer le thème clair pour tous
os.environ["STREAMLIT_THEME_BASE"] = "light"

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Trading Pro",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

# Style personnalisé (fond clair, texte foncé)
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #f9f8f4;
        color: #2e2e2e;
        font-family: 'Helvetica', sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5em 1em;
        border-radius: 6px;
    }
    .stDownloadButton>button {
        background-color: #1976D2;
        color: white;
        padding: 0.4em 1em;
        border-radius: 6px;
    }
    .stTextInput>div>div>input, .stNumberInput input {
        background-color: #fff;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Connexion aux bases de données
conn_users = sqlite3.connect("users.db", check_same_thread=False)
cur_users = conn_users.cursor()

cur_users.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')
conn_users.commit()

conn_trades = sqlite3.connect("trades.db", check_same_thread=False)
cur_trades = conn_trades.cursor()

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

# Fonctions login
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    hashed = hash_password(password)
    cur_users.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed))
    return cur_users.fetchone() is not None

def register(username, password):
    hashed = hash_password(password)
    try:
        cur_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn_users.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Initialisation session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("📊 Dashboard Trading Pro")

if not st.session_state.logged_in:
    st.subheader("🔐 Connexion ou création de compte")

    tab1, tab2 = st.tabs(["Se connecter", "Créer un compte"])

    with tab1:
        with st.form("login_form"):
            username_login = st.text_input("Nom d'utilisateur")
            password_login = st.text_input("Mot de passe", type="password")
            login_submit = st.form_submit_button("Se connecter")

            if login_submit:
                if login(username_login, password_login):
                    st.session_state.logged_in = True
                    st.session_state.username = username_login
                    st.success(f"Bienvenue {username_login} !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    with tab2:
        with st.form("register_form"):
            username_reg = st.text_input("Choisissez un nom d'utilisateur")
            password_reg = st.text_input("Choisissez un mot de passe", type="password")
            confirm_pass = st.text_input("Confirmez le mot de passe", type="password")
            reg_submit = st.form_submit_button("Créer le compte")

            if reg_submit:
                if password_reg != confirm_pass:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password_reg) < 4:
                    st.error("Mot de passe trop court.")
                elif len(username_reg.strip()) == 0:
                    st.error("Le nom d'utilisateur est vide.")
                else:
                    if register(username_reg.strip(), password_reg):
                        st.success("Inscription réussie ! Connectez-vous.")
                    else:
                        st.error("Nom d'utilisateur déjà pris.")

# Interface principale
else:
    st.success(f"Connecté en tant que : {st.session_state.username}")
    st.header("💼 Ajouter un nouveau trade")

    paires = [
        "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "BTC/USDT",
        "ETH/USDT", "XAU/USD", "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY",
        "LTC/USDT", "ADA/USDT", "DOGE/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT"
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        paire = st.selectbox("Paire", options=paires)
        direction = st.radio("Direction", ["BUY", "SELL"])
    with col2:
        capital = st.number_input("Capital (€)", min_value=0.0, value=10000.0, step=100.0)
        taille_pct = st.slider("Taille position (%)", 0.01, 100.0, 1.0)
    with col3:
        prix_entree = st.number_input("Prix d'entrée", format="%.5f")
        prix_sortie = st.number_input("Prix de sortie", format="%.5f")

    if st.button("✅ Enregistrer le trade"):
        if capital <= 0 or taille_pct <= 0 or prix_entree <= 0 or prix_sortie <= 0:
            st.error("Tous les champs doivent être valides.")
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
            st.success("✅ Trade enregistré avec succès.")

    st.divider()
    st.subheader("📈 Historique de vos trades")

    cur_trades.execute("SELECT * FROM trades WHERE username = ?", (st.session_state.username,))
    trades = cur_trades.fetchall()

    if trades:
        df = pd.DataFrame(trades, columns=["ID", "Utilisateur", "Paire", "Direction", "Taille %", "Prix entrée", "Prix sortie", "Capital"])
        df["Gain/Perte (€)"] = df.apply(lambda row: (
            (row["Prix sortie"] - row["Prix entrée"]) if row["Direction"] == "BUY" else
            (row["Prix entrée"] - row["Prix sortie"])
        ) * row["Capital"] * (row["Taille %"] / 100), axis=1)

        df["Cumulatif (€)"] = df["Gain/Perte (€)"].cumsum()

        def color_rows(row):
            return ['background-color: #d4f8d4' if row.Direction == 'BUY' else 'background-color: #f8d4d4'] * len(row)

        st.dataframe(df.style.apply(color_rows, axis=1), use_container_width=True)

        fig = px.line(df, x="ID", y="Cumulatif (€)", title="Performance cumulée")
        st.plotly_chart(fig, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Télécharger l’historique", data=csv, file_name="trades.csv", mime="text/csv")

    else:
        st.info("Aucun trade pour le moment.")

    if st.button("🚪 Se déconnecter"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()





