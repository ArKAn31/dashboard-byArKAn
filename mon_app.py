import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib

# ===== DESIGN CUSTOM =====
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #f9f8f4;
        color: #333333;
    }
    .stApp {
        background-color: #f9f8f4;
    }
    .block-container {
        padding: 2rem 3rem;
    }
    h1, h2, h3 {
        color: #2e2e2e;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        border: none;
    }
    .stTextInput>div>div>input {
        background-color: #fff;
        padding: 8px;
        border-radius: 6px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ===== DB CONNEXIONS =====
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

# ===== UTILS =====
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

# ===== CONFIG =====
st.set_page_config(page_title="Dashboard Trading Pro", layout="wide")
st.title("📊 Dashboard Trading Pro")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ===== LOGIN / SIGNUP =====
if not st.session_state.logged_in:
    st.subheader("🔐 Connexion ou Inscription")

    tab1, tab2 = st.tabs(["Se connecter", "Créer un compte"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Connexion")
            if submitted:
                if login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Bienvenue 👋")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    with tab2:
        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur", key="reg_user")
            password = st.text_input("Mot de passe", type="password", key="reg_pass")
            confirm = st.text_input("Confirmez le mot de passe", type="password")
            register_btn = st.form_submit_button("Créer mon compte")
            if register_btn:
                if password != confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 4:
                    st.error("Mot de passe trop court.")
                else:
                    if register(username.strip(), password):
                        st.success("Compte créé ✅")
                    else:
                        st.error("Nom d'utilisateur déjà utilisé.")
else:
    st.success(f"Bonjour, {st.session_state.username} 👋")

    # ===== NOUVEAU TRADE =====
    st.header("💼 Enregistrer un nouveau trade")

    paires = [
        "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "BTC/USDT",
        "ETH/USDT", "XAU/USD", "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY"
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        paire = st.selectbox("Paire", paires)
        direction = st.radio("Direction", ["BUY", "SELL"])
    with col2:
        capital = st.number_input("💰 Capital (€)", value=10000.0)
        taille_pct = st.slider("📏 Taille (%)", 0.01, 100.0, value=1.0)
    with col3:
        prix_entree = st.number_input("Prix d'entrée", format="%.5f")
        prix_sortie = st.number_input("Prix de sortie", format="%.5f")

    if st.button("💾 Enregistrer"):
        if capital > 0 and taille_pct > 0 and prix_entree > 0 and prix_sortie > 0:
            cur_trades.execute("""
                INSERT INTO trades (username, paire, direction, taille_position, prix_entree, prix_sortie, capital)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state.username,
                paire, direction,
                taille_pct, prix_entree,
                prix_sortie, capital
            ))
            conn_trades.commit()
            st.success("Trade ajouté avec succès ✅")
        else:
            st.error("Tous les champs doivent être valides.")

    # ===== HISTORIQUE =====
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
        df['Cumul (€)'] = df["Gain/Perte (€)"].cumsum()

        df_display = df[["ID", "Paire", "Direction", "Taille %", "Prix entrée", "Prix sortie", "Capital", "Gain/Perte (€)"]]
        st.dataframe(df_display.style.set_properties(**{
            'background-color': '#ffffff',
            'color': '#000000',
            'border-color': 'gray'
        }), use_container_width=True)

        fig = px.line(df, x="ID", y="Cumul (€)", title="📊 Performance cumulée")
        st.plotly_chart(fig, use_container_width=True)

        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Exporter en CSV", data=csv, file_name="trades.csv", mime="text/csv")
    else:
        st.info("Aucun trade pour l’instant.")

    if st.button("🚪 Déconnexion"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()





