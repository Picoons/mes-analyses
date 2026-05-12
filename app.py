"""
Mini-site personnel pour publier des analyses classées par catégorie.
Catégories : Géopolitique, Économie, Finance.

Lancer en local : streamlit run app.py
Déployer : pousser sur GitHub puis connecter à Streamlit Community Cloud.
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# --- Configuration de la page ---
st.set_page_config(
    page_title="Mes analyses",
    page_icon="📝",
    layout="wide",
)

# --- Stockage des articles ---
# Les articles sont stockés dans un fichier JSON local.
# Pour un usage personnel avec une seule URL, c'est largement suffisant.
DATA_FILE = Path("articles.json")
CATEGORIES = ["Géopolitique", "Économie", "Finance"]


def load_articles():
    """Charge la liste des articles depuis le fichier JSON."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_articles(articles):
    """Sauvegarde la liste des articles dans le fichier JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def add_article(title, category, content):
    """Ajoute un nouvel article."""
    articles = load_articles()
    articles.append({
        "id": int(datetime.now().timestamp()),
        "title": title,
        "category": category,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_articles(articles)


def delete_article(article_id):
    """Supprime un article par son ID."""
    articles = load_articles()
    articles = [a for a in articles if a["id"] != article_id]
    save_articles(articles)


# --- Sidebar : navigation ---
st.sidebar.title("📝 Mes analyses")
page = st.sidebar.radio(
    "Navigation",
    ["Lire les articles", "Publier un nouvel article"],
)

st.sidebar.markdown("---")
articles = load_articles()
st.sidebar.markdown(f"**Total :** {len(articles)} article(s)")
for cat in CATEGORIES:
    count = sum(1 for a in articles if a["category"] == cat)
    st.sidebar.markdown(f"- {cat} : {count}")


# --- Page 1 : Lire les articles ---
if page == "Lire les articles":
    st.title("Mes analyses")

    if not articles:
        st.info("Aucun article publié pour le moment. Va dans « Publier un nouvel article » pour commencer.")
    else:
        # Filtre par catégorie
        filter_cat = st.selectbox(
            "Filtrer par catégorie",
            ["Toutes"] + CATEGORIES,
        )

        filtered = articles if filter_cat == "Toutes" else [a for a in articles if a["category"] == filter_cat]
        # Tri du plus récent au plus ancien
        filtered = sorted(filtered, key=lambda a: a["id"], reverse=True)

        for article in filtered:
            with st.expander(f"**{article['title']}** — *{article['category']}* — {article['date']}"):
                st.markdown(article["content"])
                if st.button("🗑️ Supprimer", key=f"del_{article['id']}"):
                    delete_article(article["id"])
                    st.rerun()


# --- Page 2 : Publier un nouvel article ---
elif page == "Publier un nouvel article":
    st.title("Publier un nouvel article")

    with st.form("new_article", clear_on_submit=True):
        title = st.text_input("Titre de l'article")
        category = st.selectbox("Catégorie", CATEGORIES)
        content = st.text_area(
            "Contenu (Markdown supporté)",
            height=400,
            placeholder="Colle ton texte ici. Tu peux utiliser du Markdown : **gras**, *italique*, ## titres, etc.",
        )
        submitted = st.form_submit_button("Publier")

        if submitted:
            if not title.strip():
                st.error("Le titre ne peut pas être vide.")
            elif not content.strip():
                st.error("Le contenu ne peut pas être vide.")
            else:
                add_article(title.strip(), category, content)
                st.success(f"Article « {title} » publié dans {category} !")
