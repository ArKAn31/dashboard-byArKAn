# Utilise une image officielle avec Python
FROM python:3.11-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier les fichiers dans l'image Docker
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir streamlit pandas plotly sqlite3

# Exposer le port utilisé par Streamlit
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "mon_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
