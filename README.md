# Mes analyses

Mini-site personnel pour publier des analyses classées par catégorie (Géopolitique, Économie, Finance).

## Tester en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Le site s'ouvre dans ton navigateur sur `http://localhost:8501`.

## Déployer sur Streamlit Community Cloud (gratuit)

### 1. Créer un repo GitHub
- Va sur [github.com](https://github.com) et crée un nouveau repo (privé ou public, peu importe).
- Pousse les 3 fichiers : `app.py`, `requirements.txt`, `README.md`.

### 2. Connecter Streamlit Cloud
- Va sur [share.streamlit.io](https://share.streamlit.io) et connecte-toi avec ton compte GitHub.
- Clique sur "New app", sélectionne ton repo, branche `main`, et le fichier `app.py`.
- Clique sur "Deploy". En 2-3 minutes ton site est en ligne avec une URL du type `https://ton-projet.streamlit.app`.

### 3. Voilà
- Cette URL est unique. Si tu ne la partages pas, tu es le seul à pouvoir y accéder.
- Tu peux ajouter, lire et supprimer des articles directement depuis le navigateur.

## ⚠️ À savoir sur le stockage

Les articles sont stockés dans un fichier `articles.json` local à l'application. Sur Streamlit Cloud, ce fichier **peut être effacé si l'app redémarre** (mise à jour, inactivité prolongée).

Pour un stockage 100 % persistant, deux options simples :
1. **Google Sheets via `gspread`** : tes articles sont stockés dans un Google Sheet. Très simple à mettre en place, gratuit.
2. **Supabase (PostgreSQL gratuit)** : plus robuste, mais demande un peu plus de configuration.

Dis-moi laquelle tu veux et je te modifie le code en conséquence.
