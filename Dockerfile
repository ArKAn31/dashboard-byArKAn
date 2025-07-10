# Utiliser l'image officielle Python slim
FROM python:3.11-slim

# Installer les dépendances système nécessaires (dont sqlite3)
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer et se positionner dans le dossier /app
WORKDIR /app

# Copier les fichiers du projet dans le conteneur
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir streamlit pandas plotly

# Exposer le port 8501 (Streamlit par défaut)
EXPOSE 8501

# Commande pour lancer ton application Streamlit
CMD ["streamlit", "run", "mon_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

