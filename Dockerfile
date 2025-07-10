# Utiliser une image Python légère
FROM python:3.11-slim

# Définir le dossier de travail dans le container
WORKDIR /app

# Copier requirements.txt (à créer avec streamlit, pandas, plotly)
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'app dans le container
COPY . .

# Exposer le port 8501 (port par défaut de Streamlit)
EXPOSE 8501

# Commande pour lancer Streamlit en mode production, sans ouvrir de navigateur, et accessible de l'extérieur
CMD ["streamlit", "run", "mon_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"]

