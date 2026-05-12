"""
Mini-site personnel pour publier des analyses classées par catégorie.
Catégories : Géopolitique, Économie, Finance.

Mode lecture seule par défaut pour tous les visiteurs.
Mode admin (publier / modifier / supprimer) débloqué via mot de passe stocké dans st.secrets.

Lancer en local : streamlit run app.py
Déployer : pousser sur GitHub puis connecter à Streamlit Community Cloud.
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# --- Configuration de la page ---
st.set_page_config(
    page_title="Mes analyses",
    page_icon="📝",
    layout="wide",
)

# --- Stockage des articles ---
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


def update_article(article_id, title, category, content):
    """Met à jour un article existant."""
    articles = load_articles()
    for article in articles:
        if article["id"] == article_id:
            article["title"] = title
            article["category"] = category
            article["content"] = content
            article["date"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (modifié)"
            break
    save_articles(articles)


# --- Gestion de l'authentification admin ---
def get_admin_password():
    """
    Récupère le mot de passe admin depuis st.secrets.
    Si la clé n'existe pas, retourne None (mode admin désactivé).
    """
    try:
        return st.secrets["admin_password"]
    except (KeyError, FileNotFoundError):
        return None


# État de session : par défaut, l'utilisateur n'est pas admin
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# État de session : ID de l'article en cours d'édition (None si aucun)
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


# --- Sidebar : navigation + login admin ---
st.sidebar.title("📝 Mes analyses")

# Bloc de connexion admin
with st.sidebar.expander("🔐 Espace admin"):
    if st.session_state.is_admin:
        st.success("Connecté en admin")
        if st.button("Se déconnecter"):
            st.session_state.is_admin = False
            st.session_state.editing_id = None
            st.rerun()
    else:
        admin_pwd = get_admin_password()
        if admin_pwd is None:
            st.warning(
                "Aucun mot de passe admin défini. "
                "Configure `admin_password` dans les secrets Streamlit."
            )
        else:
            pwd_input = st.text_input("Mot de passe", type="password", key="pwd_input")
            if st.button("Se connecter"):
                if pwd_input == admin_pwd:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")

# Pages accessibles selon le mode
if st.session_state.is_admin:
    page = st.sidebar.radio(
        "Navigation",
        ["Lire les articles", "Publier un nouvel article"],
    )
else:
    page = "Lire les articles"
    st.sidebar.info("Mode lecture seule")

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
        st.info("Aucun article publié pour le moment.")
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
                # Si cet article est en cours d'édition : afficher le formulaire d'édition
                if st.session_state.is_admin and st.session_state.editing_id == article["id"]:
                    with st.form(f"edit_form_{article['id']}"):
                        new_title = st.text_input("Titre", value=article["title"])
                        new_category = st.selectbox(
                            "Catégorie",
                            CATEGORIES,
                            index=CATEGORIES.index(article["category"]),
                        )
                        new_content = st.text_area(
                            "Contenu (Markdown supporté)",
                            value=article["content"],
                            height=400,
                        )
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_clicked = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                        with col_cancel:
                            cancel_clicked = st.form_submit_button("↩️ Annuler", use_container_width=True)

                        if save_clicked:
                            if not new_title.strip():
                                st.error("Le titre ne peut pas être vide.")
                            elif not new_content.strip():
                                st.error("Le contenu ne peut pas être vide.")
                            else:
                                update_article(
                                    article["id"],
                                    new_title.strip(),
                                    new_category,
                                    new_content,
                                )
                                st.session_state.editing_id = None
                                st.rerun()
                        if cancel_clicked:
                            st.session_state.editing_id = None
                            st.rerun()

                # Sinon : affichage normal de l'article + boutons admin
                else:
                    st.markdown(article["content"])

                    if st.session_state.is_admin:
                        col_edit, col_delete, _ = st.columns([1, 1, 4])
                        with col_edit:
                            if st.button("✏️ Modifier", key=f"edit_{article['id']}"):
                                st.session_state.editing_id = article["id"]
                                st.rerun()
                        with col_delete:
                            if st.button("🗑️ Supprimer", key=f"del_{article['id']}"):
                                delete_article(article["id"])
                                st.rerun()


# --- Page 2 : Publier un nouvel article (admin uniquement) ---
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
