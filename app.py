"""
Mini-site personnel pour publier des analyses classées par catégorie.
Catégories : Géopolitique, Économie, Finance.

Mode lecture seule par défaut pour tous les visiteurs.
Mode admin (publier / modifier / supprimer) débloqué via mot de passe stocké dans st.secrets.

Supporte l'upload d'images directement dans le formulaire.
Les images sont stockées dans le dossier ./images/ et référencées en Markdown.

Lancer en local : streamlit run app.py
Déployer : pousser sur GitHub puis connecter à Streamlit Community Cloud.
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path

# --- Configuration de la page ---
st.set_page_config(
    page_title="Mes analyses",
    page_icon="📝",
    layout="wide",
)

# --- Stockage des articles et images ---
DATA_FILE = Path("articles.json")
IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(exist_ok=True)

CATEGORIES = ["Géopolitique", "Économie", "Finance"]
ALLOWED_IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "webp"]


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


def save_uploaded_image(uploaded_file):
    """
    Sauvegarde une image uploadée dans le dossier images/
    et retourne le chemin relatif pour Markdown.
    """
    extension = uploaded_file.name.split(".")[-1].lower()
    # Nom unique pour éviter les collisions
    filename = f"{uuid.uuid4().hex[:12]}.{extension}"
    filepath = IMAGES_DIR / filename
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return f"images/{filename}"


def render_article_content(content):
    """
    Affiche le contenu d'un article.
    Streamlit ne charge pas les images locales via st.markdown,
    donc on traite séparément les images locales (./images/...)
    et le reste du Markdown.
    """
    import re

    # Pattern pour détecter les images Markdown locales : ![alt](images/xxx.ext)
    pattern = r"!\[([^\]]*)\]\((images/[^)]+)\)"

    last_end = 0
    for match in re.finditer(pattern, content):
        # Affiche le texte avant l'image
        text_before = content[last_end:match.start()]
        if text_before.strip():
            st.markdown(text_before)

        # Affiche l'image
        alt_text = match.group(1)
        image_path = match.group(2)
        if Path(image_path).exists():
            st.image(image_path, caption=alt_text if alt_text else None, use_column_width=True)
        else:
            st.warning(f"Image introuvable : {image_path}")

        last_end = match.end()

    # Affiche le texte restant après la dernière image
    text_after = content[last_end:]
    if text_after.strip():
        st.markdown(text_after)


# --- Gestion de l'authentification admin ---
def get_admin_password():
    """Récupère le mot de passe admin depuis st.secrets."""
    try:
        return st.secrets["admin_password"]
    except (KeyError, FileNotFoundError):
        return None


# État de session
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
# Stocke les images uploadées en attente d'insertion (clé = ID du formulaire)
if "pending_images" not in st.session_state:
    st.session_state.pending_images = {}


# --- Sidebar : navigation + login admin ---
st.sidebar.title("📝 Mes analyses")

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
        filter_cat = st.selectbox(
            "Filtrer par catégorie",
            ["Toutes"] + CATEGORIES,
        )

        filtered = articles if filter_cat == "Toutes" else [a for a in articles if a["category"] == filter_cat]
        filtered = sorted(filtered, key=lambda a: a["id"], reverse=True)

        for article in filtered:
            with st.expander(f"**{article['title']}** — *{article['category']}* — {article['date']}"):
                # Mode édition
                if st.session_state.is_admin and st.session_state.editing_id == article["id"]:
                    # Upload d'images hors du form (pour pouvoir générer le Markdown à insérer)
                    st.markdown("**Ajouter des images à insérer dans l'article :**")
                    edit_uploader_key = f"edit_uploader_{article['id']}"
                    uploaded = st.file_uploader(
                        "Glisse une ou plusieurs images",
                        type=ALLOWED_IMAGE_TYPES,
                        accept_multiple_files=True,
                        key=edit_uploader_key,
                    )
                    if uploaded:
                        st.markdown("**Markdown à copier-coller dans le contenu :**")
                        for img_file in uploaded:
                            # Sauvegarde seulement si pas déjà fait dans cette session
                            cache_key = f"{edit_uploader_key}_{img_file.name}"
                            if cache_key not in st.session_state.pending_images:
                                path = save_uploaded_image(img_file)
                                st.session_state.pending_images[cache_key] = path
                            img_path = st.session_state.pending_images[cache_key]
                            st.code(f"![{img_file.name}]({img_path})", language="markdown")

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

                # Affichage normal
                else:
                    render_article_content(article["content"])

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

    # Upload d'images hors du form (pour pouvoir générer le Markdown à insérer)
    st.markdown("**1. Ajouter des images (optionnel)**")
    new_uploader_key = "new_article_uploader"
    uploaded = st.file_uploader(
        "Glisse une ou plusieurs images",
        type=ALLOWED_IMAGE_TYPES,
        accept_multiple_files=True,
        key=new_uploader_key,
    )
    if uploaded:
        st.markdown("**Markdown à copier-coller dans le contenu, à l'endroit où tu veux l'image :**")
        for img_file in uploaded:
            cache_key = f"{new_uploader_key}_{img_file.name}"
            if cache_key not in st.session_state.pending_images:
                path = save_uploaded_image(img_file)
                st.session_state.pending_images[cache_key] = path
            img_path = st.session_state.pending_images[cache_key]
            st.code(f"![{img_file.name}]({img_path})", language="markdown")

    st.markdown("**2. Rédiger l'article**")
    with st.form("new_article", clear_on_submit=True):
        title = st.text_input("Titre de l'article")
        category = st.selectbox("Catégorie", CATEGORIES)
        content = st.text_area(
            "Contenu (Markdown supporté)",
            height=400,
            placeholder=(
                "Colle ton texte ici. Tu peux utiliser du Markdown :\n"
                "**gras**, *italique*, ## titres, etc.\n\n"
                "Pour insérer une image : copie le code Markdown généré ci-dessus "
                "et colle-le à l'endroit voulu."
            ),
        )
        submitted = st.form_submit_button("Publier")

        if submitted:
            if not title.strip():
                st.error("Le titre ne peut pas être vide.")
            elif not content.strip():
                st.error("Le contenu ne peut pas être vide.")
            else:
                add_article(title.strip(), category, content)
                # Nettoyage des images en attente pour ce formulaire
                st.session_state.pending_images = {
                    k: v for k, v in st.session_state.pending_images.items()
                    if not k.startswith(new_uploader_key)
                }
                st.success(f"Article « {title} » publié dans {category} !")
