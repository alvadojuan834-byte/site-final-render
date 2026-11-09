from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime
import os
import csv
import urllib.parse
import urllib.request
import ast

app = Flask(__name__)
app.secret_key = 'cle_secrete_boutique_v8'

# Vraies informations de production PayPal (Live)
PAYPAL_API_USER = "alvadojuan834_api1.gmail.com"
PAYPAL_API_PWD = "6VUUOI36XVVXLICO"
PAYPAL_API_SIGNATURE = "AaRSU2y8OAIEIxg92K4Zpd.Ucl0BAZSsK.CC9mosIjzFIvsppRWx-4Y"
PAYPAL_URL = "https://api-3t.paypal.com/nvp"

# Mot de passe administrateur
ADMIN_PASSWORD = "monpassadmin123"

TRADUCTIONS = {
    "fr": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Panier", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide.", "color": "Couleur", "size": "Taille", "desc": "Description du produit", "search_placeholder": "Rechercher un produit..."},
    "be": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Panier", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide wesh.", "color": "Couleur", "size": "Taille", "desc": "Description du produit", "search_placeholder": "Rechercher un produit..."},
    "en": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Cart", "all": "All categories", "buy": "Buy Now", "total": "Total", "checkout": "🔒 Checkout", "empty": "Your cart is empty.", "color": "Color", "size": "Size", "desc": "Product description", "search_placeholder": "Search a product..."},
    "de": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Warenkorb", "all": "Alle Kategorien", "buy": "Kaufen", "total": "Gesamt", "checkout": "🔒 Zur Kasse", "empty": "Ihr Warenkorb ist leer.", "color": "Farbe", "size": "Größe", "desc": "Produktbeschreibung", "search_placeholder": "Produkt suchen..."},
    "es": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Carrito", "all": "Todas las categorías", "buy": "Comprar", "total": "Total", "checkout": "🔒 Tramitar pedido", "empty": "Tu carrito está vacío.", "color": "Color", "talla": "Talla", "desc": "Descripción del producto", "search_placeholder": "Buscar un producto..."},
    "nl": {"shop": "MonShop Direct", "promo": "🔥 Catalogue Direct ✨", "cart": "Winkelmand", "all": "Alle categorieën", "buy": "Kopen", "total": "Totaal", "checkout": "🔒 Afrekenen", "empty": "Je winkelmand is leeg.", "color": "Kleur", "size": "Maat", "desc": "Produktbeschrijving", "search_placeholder": "Zoek een product..."}
}

CATEGORIES = {
    "telephonie": "📱 Téléphonie & Audio",
    "chauffage": "🔥 Chauffage & Maison",
    "cuisine": "🍳 Cuisine & Ustensiles",
    "sport": "⚽ Sport & Loisirs",
    "eclairage": "💡 Éclairage & Auto",
    "mode": "👕 Mode & Accessoires",
    "beaute": "💄 Beauté & Santé",
    "bricolage": "🛠️ Bricolage & Outils",
    "jardin": "🌱 Jardin & Extérieur",
    "animaux": "🐾 Animaux de compagnie",
    "gaming": "🎮 Gaming & High-Tech",
    "general": "✨ Tendances Générales"
}

LOCAL_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "produits_etat.csv")

def determiner_categorie(nom_produit):
    nom = nom_produit.lower()
    if any(k in nom for k in ['phone', 'tel', 'audio', 'écouteur', 'casque', 'bluetooth', 'cable', 'chargeur', 'montre', 'smartwatch']):
        return "telephonie"
    elif any(k in nom for k in ['chauffage', 'radiateur', 'ventilateur', 'maison', 'lampe', 'lumière', 'ampoule', 'led']):
        return "chauffage"
    elif any(k in nom for k in ['cuisine', 'gant', 'silicone', 'tasse', 'bouteille', 'gourde', 'coupe', 'poêle', 'casserole', 'moule']):
        return "cuisine"
    elif any(k in nom for k in ['sport', 'fitness', 'musculation', 'vélo', 'yoga', 'camping', 'plein air', 'loisir']):
        return "sport"
    elif any(k in nom for k in ['auto', 'voiture', 'caméra', 'rétroviseur', 'clé', 'outil auto']):
        return "eclairage"
    elif any(k in nom for k in ['chemise', 'pantalon', 'robe', 'chaussure', 'sac', 'portefeuille', 'vêtement', 'pull', 'veste', 'lunettes']):
        return "mode"
    elif any(k in nom for k in ['maquillage', 'brosse', 'cheveux', 'soin', 'crème', 'rasoir', 'épilateur', 'parfum', 'ongle', 'miroir']):
        return "beaute"
    elif any(k in nom for k in ['perceuse', 'tournevis', 'vis', 'marteau', 'bricolage', 'mètre', 'pince', 'scie', 'quincaillerie']):
        return "bricolage"
    elif any(k in nom for k in ['jardin', 'plante', 'fleur', 'arrosage', 'tuyau', 'terrasse', 'solaire', 'barbecue', 'piscine']):
        return "jardin"
    elif any(k in nom for k in ['chat', 'chien', 'animal', 'croquette', 'laisse', 'collier', 'niche', 'litière', 'jouet pour chat']):
        return "animaux"
    elif any(k in nom for k in ['gaming', 'clavier', 'souris', 'manette', 'pc', 'gamer', 'console', 'jeu vidéo', 'micro']):
        return "gaming"
    return "general"

def parser_dossier_csv():
    produits_importes = []
    dossier_csv = r"C:\csv.aliexpress"
    if not os.path.exists(dossier_csv):
        return []

    c = 1
    for fichier in os.listdir(dossier_csv):
        if fichier.endswith(".csv"):
            chemin_complet = os.path.join(dossier_csv, fichier)
            try:
                with open(chemin_complet, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                    lecteur = csv.DictReader(f)
                    for ligne in lecteur:
                        nom = ligne.get('Title') or ligne.get('nom') or 'Produit AliExpress'
                        prix = ligne.get('Sale price') or ligne.get('prix') or '19.99'
                        if not prix: prix = '19.99'
                        image = ligne.get('Product Image Url') or ligne.get('image') or 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500'
                        if ',' in image: image = image.split(',')[0].strip()
                        galerie_raw = ligne.get('Main images url') or ligne.get('galerie') or ''
                        galerie = [img.strip() for img in galerie_raw.split(',') if img.strip()]
                        if not galerie: galerie = [image]
                        desc = ligne.get('Product description html') or ligne.get('description') or 'Aucune description disponible.'
                        
                        cat = determiner_categorie(nom)
                        produits_importes.append({
                            "id": c, "nom": nom, "prix": str(prix), "image": image,
                            "galerie": galerie[:5], "categorie": cat, "description": str(desc)[:300] + "..."
                        })
                        c += 1
            except Exception as e:
                print(f"Erreur lecture {fichier}: {e}")
    return produits_importes

def charger_produits():
    produits = []
    if os.path.exists(LOCAL_STATE_FILE):
        try:
            with open(LOCAL_STATE_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['id'] = int(row['id'])
                    galerie_raw = row.get('galerie', '')
                    if galerie_raw.startswith('['):
                        try:
                            row['galerie'] = ast.literal_eval(galerie_raw)
                        except:
                            row['galerie'] = [row.get('image', '')]
                    else:
                        row['galerie'] = [img.strip() for img in galerie_raw.split(',') if img.strip()]
                    produits.append(row)
        except:
            pass

    if not produits:
        produits = parser_dossier_csv()
        if not produits:
            produits = [{
                "id": 1, "nom": "Radiateur Électrique à Convection 2000W", "prix": "49.99",
                "image": "https://images.unsplash.com/photo-1585338107529-13afc5f02586?w=500",
                "galerie": ["https://images.unsplash.com/photo-1585338107529-13afc5f02586?w=500"],
                "categorie": "chauffage", "description": "Description par défaut."
            }]
        sauvegarder_produits(produits)
    return produits

def sauvegarder_produits(produits):
    os.makedirs(os.path.dirname(LOCAL_STATE_FILE), exist_ok=True)
    with open(LOCAL_STATE_FILE, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'nom', 'prix', 'image', 'galerie', 'categorie', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in produits:
            p_copy = p.copy()
            p_copy['galerie'] = str(p_copy['galerie'])
            writer.writerow(p_copy)

PRODUITS = charger_produits()
COMMANDES = []

CSS_STYLED = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; }
    .header { background: linear-gradient(135deg, #2e1065 0%, #4c1d95 100%); color: white; padding: 18px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); flex-wrap: wrap; gap: 15px; }
    .brand-logo { font-size: 20px; font-weight: 800; color: white; text-decoration: none; display: flex; align-items: center; gap: 8px; }
    .search-form { display: flex; gap: 5px; flex-grow: 1; max-width: 350px; }
    .search-form input[type="text"] { width: 100%; padding: 8px 14px; border-radius: 6px; border: none; font-size: 14px; outline: none; }
    .search-form button { background: #ff9900; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; }
    .promo-banner { font-size: 15px; font-weight: 800; color: #ffffff; background: rgba(255, 255, 255, 0.1); padding: 6px 16px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.2); }
    .nav-actions { display: flex; align-items: center; gap: 15px; }
    .lang-select { background: #581c87; color: white; border: 1px solid #7c3aed; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .cart-btn { background: #e11d48; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px; }
    .cart-badge { background: white; color: #e11d48; border-radius: 50%; padding: 1px 7px; font-size: 12px; font-weight: 900; }
    .top-trust-bar { background: #ffffff; border-bottom: 1px solid #e5e7eb; padding: 12px 30px; display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .trust-item { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 700; color: #374155; }
    .trust-item span { font-size: 18px; }
    .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
    .cat-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 25px; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .cat-tag { background: #e2e8f0; color: #334155; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-size: 13px; font-weight: 700; transition: all 0.2s; }
    .cat-tag:hover, .cat-tag.active { background: #6d28d9; color: white; }
    .sec-header { font-size: 20px; font-weight: 800; color: #2e1065; margin: 35px 0 15px 0; border-bottom: 2px solid #e9d5ff; padding-bottom: 8px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
    .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); display: flex; flex-direction: column; border: 1px solid #f3f4f6; }
    .card-img-wrap { height: 190px; overflow: hidden; background: #f8fafc; display: block; }
    .card-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
    .card-body { padding: 15px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between; }
    .card-title { font-size: 13px; font-weight: 700; color: #1f2937; margin-bottom: 10px; text-decoration: none; height: 40px; overflow: hidden; display: block; }
    .card-price { font-size: 18px; font-weight: 900; color: #2563eb; margin-bottom: 12px; }
    .btn-buy { background: #6d28d9; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; text-decoration: none; text-align: center; display: block; width: 100%; }
    .btn-paypal { background: #0070ba; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; text-decoration: none; text-align: center; display: block; width: 100%; }
</style>
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>MonShop Direct</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <form action="/" method="GET" class="search-form">
            <input type="hidden" name="lang" value="{{ lang }}">
            {% if active_cat %}<input type="hidden" name="cat" value="{{ active_cat }}">{% endif %}
            <input type="text" name="q" value="{{ search_query }}" placeholder="{{ t.search_placeholder }}">
            <button type="submit">🔍</button>
        </form>
        <div class="nav-actions">
            <form action="/set_lang" method="POST" style="margin:0;">
                <select name="lang" class="lang-select" onchange="this.form.submit()">
                    <option value="fr" {% if lang == 'fr' %}selected{% endif %}>🇫🇷 FR</option>
                    <option value="be" {% if lang == 'be' %}selected{% endif %}>🇧🇪 BE</option>
                    <option value="en" {% if lang == 'en' %}selected{% endif %}>🇬🇧 EN</option>
                    <option value="de" {% if lang == 'de' %}selected{% endif %}>🇩🇪 DE</option>
                    <option value="es" {% if lang == 'es' %}selected{% endif %}>🇪🇸 ES</option>
                    <option value="nl" {% if lang == 'nl' %}selected{% endif %}>🇳🇱 NL</option>
                </select>
            </form>
            <a href="/cart?lang={{ lang }}" class="cart-btn">🛒 {{ t.cart }} {% if session.get('cart', []) %}<span class="cart-badge">{{ session.get('cart', [])|length }}</span>{% endif %}</a>
        </div>
    </div>
    <div class="top-trust-bar">
        <div class="trust-item"><span>🔒</span> Paiement 100% sécurisé</div>
        <div class="trust-item"><span>📦</span> Suivi des colis en temps réel</div>
        <div class="trust-item"><span>⚡</span> Expédition rapide garantie</div>
    </div>
    <div class="container">
        <div class="cat-bar">
            <a href="/?lang={{ lang }}{% if search_query %}&q={{ search_query }}{% endif %}" class="cat-tag {% if not active_cat %}active{% endif %}">🔥 {{ t.all }}</a>
            {% for slug, nom in categories.items() %}
            <a href="/?cat={{ slug }}&lang={{ lang }}{% if search_query %}&q={{ search_query }}{% endif %}" class="cat-tag {% if active_cat == slug %}active{% endif %}">{{ nom }}</a>
            {% endfor %}
        </div>
        <div class="sec-header">Catalogue Direct ✨ {% if active_cat %}- {{ categories.get(active_cat, '') }}{% endif %} ({{ produits|length }} articles)</div>
        <div class="grid">
            {% for p in produits %}
            <div class="card">
                <a href="/product/{{ p.id }}?lang={{ lang }}" class="card-img-wrap"><img src="{{ p.image }}" alt=""></a>
                <div class="card-body">
                    <a href="/product/{{ p.id }}?lang={{ lang }}" class="card-title">{{ p.nom }}</a>
                    <div class="card-price">{{ p.prix }} €</div>
                    <form action="/add/{{ p.id }}?lang={{ lang }}" method="POST"><button type="submit" class="btn-buy">{{ t.buy }}</button></form>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

HTML_PRODUCT = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>{{ p.nom }}</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <div class="promo-banner">{{ t.promo }}</div>
        <a href="/?lang={{ lang }}" style="color:white; text-decoration:none; font-weight:bold;">⬅️ Retour</a>
    </div>
    <div class="container">
        <div style="background: white; border-radius: 12px; padding: 30px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 20px;">
            <div>
                <img src="{{ p.image }}" id="mainImg" style="width: 100%; height: 380px; object-fit: cover; border-radius: 8px;">
                <div style="display: flex; gap: 10px; margin-top: 15px; overflow-x: auto;">
                    {% for img in p.galerie %}
                    <img src="{{ img }}" style="width: 70px; height: 70px; object-fit: cover; border-radius: 6px; cursor: pointer;" onclick="document.getElementById('mainImg').src = this.src">
                    {% endfor %}
                </div>
            </div>
            <div>
                <h1 style="font-size: 22px; font-weight: 800; margin-bottom: 12px;">{{ p.nom }}</h1>
                <div style="font-size: 28px; font-weight: 900; color: #2563eb; margin-bottom: 20px;">{{ p.prix }} €</div>
                <div style="color: #4b5563; font-size: 13px; line-height: 1.6; margin-bottom: 25px;">{{ p.description | safe }}</div>
                <form action="/add/{{ p.id }}?lang={{ lang }}" method="POST">
                    <button type="submit" class="btn-buy" style="padding: 14px; font-size: 16px;">{{ t.buy }}</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_CART = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>Panier</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <div class="promo-banner">{{ t.promo }}</div>
        <a href="/?lang={{ lang }}" style="color:white; text-decoration:none; font-weight:bold;">Continuer</a>
    </div>
    <div class="container" style="max-width: 800px;">
        <div style="background:white; border-radius: 12px; padding: 30px;">
            <h2 style="color: #2e1065; margin-bottom: 20px;">{{ t.cart }}</h2>
            {% if cart %}
                {% for item in cart %}
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #f1f5f9; padding: 15px 0;">
                    <img src="{{ item.image }}" style="width:70px; height:70px; object-fit:cover; border-radius:8px;">
                    <div style="flex-grow:1; margin-left: 20px; font-weight:700; font-size:14px;">{{ item.nom }}</div>
                    <div style="font-weight:900; font-size:18px; color:#2563eb; margin-right: 25px;">{{ item.prix }} €</div>
                    <a href="/remove/{{ loop.index0 }}?lang={{ lang }}" style="color:#ef4444; font-weight:bold; text-decoration:none;">Supprimer</a>
                </div>
                {% endfor %}
                <div style="text-align:right; font-size:24px; font-weight:900; margin-top:25px; color:#2e1065;">{{ t.total }} : {{ "%.2f"|format(total) }} €</div>
                <div style="display:flex; justify-content:space-between; margin-top:30px; align-items:center;">
                    <a href="/clear?lang={{ lang }}" style="color:#64748b; font-weight:bold; text-decoration:none;">Vider le panier</a>
                    <a href="/checkout?lang={{ lang }}" class="btn-buy" style="width:auto; padding: 14px 28px; background:#16a34a; font-size:16px;">{{ t.checkout }}</a>
                </div>
            {% else %}
                <p style="text-align:center; padding: 40px; color:#64748b; font-weight:600;">{{ t.empty }}</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

HTML_CHECKOUT = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Validation Commande</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/" class="brand-logo">🛍️ MonShop Direct</a>
        <div class="promo-banner">🔥 Paiement Sécurisé</div>
        <a href="/cart" style="color:white; text-decoration:none; font-weight:bold;">⬅️ Panier</a>
    </div>
    <div class="container" style="max-width: 650px;">
        <div style="background:white; border-radius: 12px; padding: 30px;">
            <h2 style="color: #2e1065; margin-bottom: 10px;">💳 Paiement Sécurisé via PayPal</h2>
            <form action="/process_order" method="POST">
                <div style="margin-bottom: 15px;"><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Nom et Prénom</label><input type="text" name="nom" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <div style="margin-bottom: 15px;"><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Adresse postale</label><input type="text" name="adresse" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                    <div><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Code Postal</label><input type="text" name="cp" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                    <div><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Ville</label><input type="text" name="ville" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                </div>
                <div style="margin-bottom: 15px;"><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Pays</label><input type="text" name="pays" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <div style="margin-bottom: 25px;"><label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Téléphone</label><input type="tel" name="tel" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <button type="submit" class="btn-paypal">🅿️ Payer avec PayPal</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Commande Validée</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header"><a href="/" class="brand-logo">🛍️ MonShop Direct</a></div>
    <div class="container" style="max-width: 750px;">
        <div style="background:white; border-radius: 12px; padding: 40px; text-align: center;">
            <div style="font-size: 50px; margin-bottom: 15px;">🎉</div>
            <h2 style="color: #16a34a; font-size: 26px; margin-bottom: 10px;">Paiement PayPal validé avec succès !</h2>
            <p style="color: #64748b; margin-bottom: 30px;">Merci <strong>{{ commande.nom }}</strong>.</p>
            <a href="/" class="btn-buy" style="display:inline-block; width:auto; padding: 12px 30px;">Retourner à la boutique</a>
        </div>
    </div>
</body>
</html>
"""

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Connexion Admin</title>""" + CSS_STYLED + """</head>
<body>
    <div class="container" style="max-width: 400px; margin-top: 100px;">
        <div style="background: white; padding: 30px; border-radius: 12px; text-align: center;">
            <h2 style="color: #2e1065; margin-bottom: 20px;">🔐 Administration</h2>
            {% if erreur %}<p style="color: #ef4444; font-size: 13px; margin-bottom: 15px; font-weight: bold;">{{ erreur }}</p>{% endif %}
            <form action="/admin/login" method="POST">
                <input type="password" name="password" required placeholder="Mot de passe admin" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 15px;">
                <button type="submit" style="width: 100%; background: #6d28d9; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer;">Se connecter</button>
            </form>
            <a href="/" style="display: block; margin-top: 20px; color: #64748b; font-size: 12px; text-decoration: none;">⬅️ Retour</a>
        </div>
    </div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Administration</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/admin" class="brand-logo">🛍️ ADMIN SHOP</a>
        <div style="display: flex; gap: 15px; align-items: center;">
            <a href="/" style="color:white; text-decoration:none; font-weight:bold;">Voir le site ➡️</a>
            <a href="/admin/logout" style="background: #ef4444; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold;">Déconnexion</a>
        </div>
    </div>
    <div class="container">
        <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
            <h3 style="color: #2e1065; margin-bottom: 10px;">📂 Importer un fichier CSV</h3>
            <form action="/admin/import_csv" method="POST" enctype="multipart/form-data" style="display: flex; gap: 15px; align-items: center;">
                <input type="file" name="fichier_csv" accept=".csv" required style="padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;">
                <button type="submit" style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;">📥 Importer</button>
            </form>
        </div>
        <div style="background: white; padding: 25px; border-radius: 12px;">
            <h3 style="color: #2e1065; margin-bottom: 15px;">⚙️ Gestion des produits ({{ produits|length }} articles)</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr style="border-bottom: 2px solid #e2e8f0; text-align: left;"><th style="padding: 10px;">ID</th><th style="padding: 10px;">Nom</th><th style="padding: 10px;">Prix</th><th style="padding: 10px;">Catégorie</th><th style="padding: 10px;">Action</th></tr>
                {% for p in produits %}
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 10px;">{{ p.id }}</td>
                    <td style="padding: 10px; font-weight: bold;">{{ p.nom }}</td>
                    <td style="padding: 10px; color: #2563eb;">{{ p.prix }} €</td>
                    <td style="padding: 10px; color: #6d28d9;">{{ categories.get(p.categorie, p.categorie) }}</td>
                    <td style="padding: 10px;"><a href="/admin/delete/{{ p.id }}" style="color: #ef4444; font-weight: bold; text-decoration: none;">Supprimer</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    lang = session.get('lang', 'fr')
    t = TRADUCTIONS.get(lang, TRADUCTIONS['fr'])
    cat_filtre = request.args.get('cat')
    query = request.args.get('q', '').strip().lower()
    produits_A_afficher = PRODUITS
    if cat_filtre:
        produits_A_afficher = [p for p in produits_A_afficher if p['categorie'] == cat_filtre]
    if query:
        produits_A_afficher = [p for p in produits_A_afficher if query in p['nom'].lower() or query in p['description'].lower()]
    return render_template_string(HTML_INDEX, produits=produits_A_afficher, categories=CATEGORIES, active_cat=cat_filtre, lang=lang, t=t, search_query=request.args.get('q', ''))

@app.route('/product/<int:p_id>')
def product(p_id):
    lang = session.get('lang', 'fr')
    p = next((item for item in PRODUITS if item["id"] == p_id), None)
    if not p: return redirect(url_for('home'))
    return render_template_string(HTML_PRODUCT, p=p, lang=lang, t=TRADUCTIONS.get(lang, TRADUCTIONS['fr']))

@app.route('/set_lang', methods=['POST'])
def set_lang():
    session['lang'] = request.form.get('lang', 'fr')
    return redirect(url_for('home'))

@app.route('/add/<int:p_id>', methods=['POST'])
def add(p_id):
    lang = request.args.get('lang', 'fr')
    if 'cart' not in session: session['cart'] = []
    p = next((item for item in PRODUITS if item["id"] == p_id), None)
    if p:
        session['cart'].append(p)
        session.modified = True
    return redirect(url_for('cart', lang=lang))

@app.route('/cart')
def cart():
    lang = request.args.get('lang', 'fr')
    items = session.get('cart', [])
    total = sum(float(item['prix']) for item in items if item['prix'].replace('.','',1).isdigit())
    return render_template_string(HTML_CART, cart=items, total=total, lang=lang, t=TRADUCTIONS.get(lang, TRADUCTIONS['fr']))

@app.route('/remove/<int:index>')
def remove(index):
    lang = request.args.get('lang', 'fr')
    if 'cart' in session and 0 <= index < len(session['cart']):
        session['cart'].pop(index)
        session.modified = True
    return redirect(url_for('cart', lang=lang))

@app.route('/clear')
def clear():
    lang = request.args.get('lang', 'fr')
    session.pop('cart', None)
    return redirect(url_for('cart', lang=lang))

@app.route('/checkout')
def checkout():
    items = session.get('cart', [])
    if not items: return redirect(url_for('home'))
    total = sum(float(item['prix']) for item in items if item['prix'].replace('.','',1).isdigit())
    return render_template_string(HTML_CHECKOUT, total=total)

@app.route('/process_order', methods=['POST'])
def process_order():
    items = session.get('cart', [])
    if not items:
        return redirect(url_for('home'))
    total = sum(float(item['prix']) for item in items if item['prix'].replace('.','',1).isdigit())
    
    nom = request.form.get('nom')
    adresse = request.form.get('adresse')
    cp = request.form.get('cp')
    ville = request.form.get('ville')
    pays = request.form.get('pays')
    tel = request.form.get('tel')

    montant_str = f"{total:.2f}"
    
    data = {
        "USER": PAYPAL_API_USER,
        "PWD": PAYPAL_API_PWD,
        "SIGNATURE": PAYPAL_API_SIGNATURE,
        "METHOD": "SetExpressCheckout",
        "VERSION": "124.0",
        "PAYMENTREQUEST_0_AMT": montant_str,
        "PAYMENTREQUEST_0_CURRENCYCODE": "EUR",
        "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
        "RETURNURL": request.host_url + "paypal_success",
        "CANCELURL": request.host_url + "cart"
    }
    
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(PAYPAL_URL, data=encoded_data, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            parsed = urllib.parse.parse_qs(res_body)
            if parsed.get('ACK', [''])[0] == 'Success':
                token = parsed.get('TOKEN', [''])[0]
                session['paypal_token'] = token
                session['order_info'] = {"nom": nom, "adresse": adresse, "cp": cp, "ville": ville, "pays": pays, "tel": tel}
                return redirect(f"https://www.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token={token}")
    except Exception as e:
        print("Erreur PayPal NVP Live:", e)

    commande = {"nom": nom}
    session.pop('cart', None)
    return render_template_string(HTML_SUCCESS, commande=commande)

@app.route('/paypal_success')
def paypal_success():
    commande = session.get('order_info', {"nom": "Client"})
    session.pop('cart', None)
    return render_template_string(HTML_SUCCESS, commande=commande)

@app.route('/admin')
def admin():
    if not session.get('admin_logged'): return redirect(url_for('admin_login'))
    return render_template_string(HTML_ADMIN, produits=PRODUITS, categories=CATEGORIES)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    erreur = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect(url_for('admin'))
        else:
            erreur = "Mot de passe incorrect."
    return render_template_string(HTML_LOGIN, erreur=erreur)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:p_id>')
def admin_delete(p_id):
    if not session.get('admin_logged'): return redirect(url_for('admin_login'))
    global PRODUITS
    PRODUITS = [p for p in PRODUITS if p['id'] != p_id]
    sauvegarder_produits(PRODUITS)
    return redirect(url_for('admin'))

@app.route('/admin/import_csv', methods=['POST'])
def admin_import_csv():
    if not session.get('admin_logged'): return redirect(url_for('admin_login'))
    if 'fichier_csv' not in request.files: return redirect(url_for('admin'))
    f = request.files['fichier_csv']
    if f.filename != '':
        try:
            contenu = f.read().decode('utf-8-sig', errors='ignore').splitlines()
            lecteur = csv.DictReader(contenu)
            global PRODUITS
            max_id = max([p['id'] for p in PRODUITS], default=0)
            for ligne in lecteur:
                max_id += 1
                nom = ligne.get('Title') or ligne.get('nom') or 'Produit AliExpress'
                prix = ligne.get('Sale price') or ligne.get('prix') or '19.99'
                if not prix: prix = '19.99'
                image = ligne.get('Product Image Url') or ligne.get('image') or 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500'
                if ',' in image: image = image.split(',')[0].strip()
                galerie_raw = ligne.get('Main images url') or ligne.get('galerie') or ''
                galerie = [img.strip() for img in galerie_raw.split(',') if img.strip()]
                if not galerie: galerie = [image]
                desc = ligne.get('Product description html') or ligne.get('description') or 'Aucune description disponible.'
                cat = determiner_categorie(nom)
                PRODUITS.append({
                    "id": max_id, "nom": nom, "prix": str(prix), "image": image,
                    "galerie": galerie[:5], "categorie": cat, "description": str(desc)[:300] + "..."
                })
            sauvegarder_produits(PRODUITS)
        except Exception as e:
            print("Erreur:", e)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
