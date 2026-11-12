from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime
import os
import csv
import urllib.parse
import urllib.request
import ast
import io
import stripe

app = Flask(__name__)
app.secret_key = 'cle_secrete_boutique_v8'

# Clés officielles (nettoyées pour éviter le blocage GitHub)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

DARKGPT_URL = 'https://darkgpt.chat/chat'
DARKGPT_KEY = 'Dgpt_live_f8c09fb91710df4fdb3b7f5d54a8a57c77bbdb1e98e0c008'

PAYPAL_API_USER = "alvadojuan834_api1.gmail.com"
PAYPAL_API_PWD = "6VUUOI36XVVXLICO"
PAYPAL_API_SIGNATURE = "AaRSU2y8OAIEIxg92K4Zpd.Ucl0BAZSsK.CC9mosIjzFIvsppRWx-4Y"
PAYPAL_URL = "https://api-3t.paypal.com/nvp"

ADMIN_PASSWORD = "monpassadmin123"

TRADUCTIONS = {
    "fr": {"shop": "Mon Shop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Panier", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide.", "color": "Couleur", "size": "Taille", "desc": "Description du produit", "search_placeholder": "Rechercher un produit..."},
    "be": {"shop": "Mon Shop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Panier", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide wesh.", "color": "Couleur", "size": "Taille", "desc": "Description du produit", "search_placeholder": "Rechercher un produit..."},
    "en": {"shop": "Mon Shop Direct", "promo": "🔥 AliExpress Boost Promos 🔥", "cart": "Cart", "all": "All categories", "buy": "Buy Now", "total": "Total", "checkout": "🔒 Checkout", "empty": "Your cart is empty.", "color": "Color", "size": "Size", "desc": "Product description", "search_placeholder": "Search a product..."},
    "de": {"shop": "Mon Shop Direct", "promo": "🔥 AliExpress Boost Angebote 🔥", "cart": "Warenkorb", "all": "Alle Kategorien", "buy": "Kaufen", "total": "Gesamt", "checkout": "🔒 Zur Kasse", "empty": "Ihr Warenkorb ist leer.", "color": "Farbe", "size": "Größe", "desc": "Produktbeschreibung", "search_placeholder": "Produkt suchen..."},
    "es": {"shop": "Mon Shop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Carrito", "all": "Todas las categorías", "buy": "Comprar", "total": "Total", "checkout": "🔒 Tramitar pedido", "empty": "Tu carrito está vacío.", "color": "Color", "talla": "Talla", "desc": "Descripción del producto", "search_placeholder": "Buscar un producto..."},
    "nl": {"shop": "Mon Shop Direct", "promo": "🔥 AliExpress Boost Promo's 🔥", "cart": "Winkelmand", "all": "Alle categorieën", "buy": "Kopen", "total": "Totaal", "checkout": "🔒 Afrekenen", "empty": "Je winkelmand is leeg.", "color": "Kleur", "size": "Maat", "desc": "Produktbeschrijving", "search_placeholder": "Zoek een product..."}
}

CATEGORIES = {
    "hifi": "🎧 Hi-Fi & Audio",
    "pc": "💻 PC & Informatique",
    "gaming": "🎮 Gaming & Consoles",
    "pokemon": "⚡ Cartes & Goodies Pokémon",
    "telephonie": "📱 Téléphonie & Accessoires",
    "chauffage": "🔥 Chauffage & Confort",
    "sport": "⚽ Sport & Loisirs",
    "eclairage": "💡 Éclairage & Auto",
    "vetements_homme": "👔 Vêtements Hommes",
    "vetements_femme": "👗 Vêtements Femmes",
    "bijoux": "💍 Bijoux & Montres",
    "sacs": "👜 Sacs & Maroquinerie",
    "beaute": "💄 Beauté & Soins",
    "general": "✨ Tendances Générales"
}

LOCAL_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mes_produits_sauves.csv")

def calculer_prix_marge(prix_brut_str):
    try:
        nettoye = ''.join(c for c in str(prix_brut_str) if c.isdigit() or c in ['.', ','])
        prix_base = float(nettoye.replace(',', '.'))
    except:
        return "19.99"
    
    if prix_base < 15.0:
        prix_final = prix_base * 2.0
    elif prix_base <= 100.0:
        prix_final = prix_base + 15.0
    else:
        prix_final = prix_base + 30.0
        
    return f"{prix_final:.2f}"

def parser_ligne_produit(ligne, current_id):
    # Sécurité renforcée pour récupérer le vrai nom du produit peu importe le format de la colonne CSV
    nom = (
        ligne.get('Title') or 
        ligne.get('Product Name') or 
        ligne.get('subject') or 
        ligne.get('nom') or 
        ligne.get('Product Title') or
        'Produit AliExpress'
    )
    if not nom or nom == 'nan':
        nom = 'Produit AliExpress'
    
    prix_brut = (
        ligne.get('Sale price') or 
        ligne.get('Sale price formatted') or 
        ligne.get('price') or 
        ligne.get('Price') or 
        ligne.get('prix') or 
        ligne.get('Product Price') or 
        '19.99'
    )
    if not prix_brut or prix_brut == 'nan': 
        prix_brut = '19.99'
    
    prix = calculer_prix_marge(prix_brut)

    image = ligne.get('Product Image Url') or ligne.get('image') or 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500'
    if ',' in image: image = image.split(',')[0].strip()
    galerie_raw = ligne.get('Main images url') or ligne.get('galerie') or ''
    galerie = [img.strip() for img in galerie_raw.split(',') if img.strip()]
    if not galerie or galerie == ['nan']: galerie = [image]
    
    desc_brute = ligne.get('Product description html') or ligne.get('description') or ''
    
    nom_lower = nom.lower()
    desc_lower = str(desc_brute).lower()
    texte_complet = nom_lower + " " + desc_lower
    
    if any(k in texte_complet for k in ['pokemon', 'pokémon', 'card', 'carte']):
        categorie = "pokemon"
    elif any(k in texte_complet for k in ['gaming', 'gamer', 'clavier', 'souris', 'manette', 'headset', 'ps5', 'xbox']):
        categorie = "gaming"
    elif any(k in texte_complet for k in ['pc', 'ordinateur', 'laptop', 'ecran', 'cpu']):
        categorie = "pc"
    elif any(k in texte_complet for k in ['hifi', 'audio', 'casque', 'ecouteurs', 'enceinte', 'bluetooth', 'soundbar', 'mp3']):
        categorie = "hifi"
    elif any(k in texte_complet for k in ['telephone', 'smartphone', 'chargeur', 'cable', 'iphone', 'samsung']):
        categorie = "telephonie"
    elif any(k in texte_complet for k in ['chauffage', 'radiateur', 'ventilateur', 'climatisation']):
        categorie = "chauffage"
    elif any(k in texte_complet for k in ['sport', 'fitness', 'velo', 'musculation']):
        categorie = "sport"
    elif any(k in texte_complet for k in ['lampe', 'eclairage', 'led', 'auto', 'voiture']):
        categorie = "eclairage"
    elif any(k in texte_complet for k in ['bijou', 'bague', 'collier', 'bracelet', 'montre', 'jewelry', 'watch', 'ring', 'necklace']):
        categorie = "bijoux"
    elif any(k in texte_complet for k in ['sac', 'portefeuille', 'sac à main', 'bag', 'wallet', 'backpack']):
        categorie = "sacs"
    elif any(k in texte_complet for k in ['maquillage', 'parfum', 'creme', 'soin', 'beaute', 'makeup', 'beauty']):
        categorie = "beaute"
    elif any(k in texte_complet for k in ['robe', 'jupe', 'femme', 'talon', 'blouse', 'women', 'dress', 'lady']):
        categorie = "vetements_femme"
    elif any(k in texte_complet for k in ['homme', 't-shirt', 'pantalon', 'veste', 'pull', 'sweat', 'chemise', 'hoodie', 'men', 'jacket']):
        categorie = "vetements_homme"
    else:
        categorie = "general"

    desc = str(desc_brute) if desc_brute and desc_brute != 'nan' else f"Description officielle pour {nom}."

    variantes_couleur = ["Noir Mat", "Blanc Pur", "Édition Limitée", "Gris Sidéral"]
    variantes_taille = ["S", "M", "L", "XL", "Standard"] if categorie in ["vetements_homme", "vetements_femme"] else ["Standard", "Universel"]
    
    return {
        "id": current_id, 
        "nom": nom, 
        "prix": str(prix), 
        "image": image,
        "galerie": galerie[:5], 
        "categorie": categorie, 
        "description": str(desc)[:1500],
        "couleur": variantes_couleur[current_id % len(variantes_couleur)],
        "taille": variantes_taille[current_id % len(variantes_taille)]
    }

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
                    
                    prix_actuel = row.get('prix', '19.99')
                    row['prix'] = calculer_prix_marge(prix_actuel)
                    if 'couleur' not in row: row['couleur'] = "Standard"
                    if 'taille' not in row: row['taille'] = "Unique"
                    produits.append(row)
            if produits:
                return produits
        except Exception as e:
            print(f"Erreur chargement etat local: {e}")

    produits_importes = []
    chemin_csv = "mes_produits_sauves.csv"
    if os.path.exists(chemin_csv):
        try:
            with open(chemin_csv, mode='r', encoding='utf-8') as f:
                lecteur = csv.DictReader(f)
                for idx, ligne in enumerate(lecteur):
                    produits_importes.append(parser_ligne_produit(ligne, idx))
        except Exception as e:
            print(f"Erreur lecture {chemin_csv}: {e}")
            
    return produits_importes

def sauvegarder_produits(produits):
    os.makedirs(os.path.dirname(LOCAL_STATE_FILE), exist_ok=True)
    with open(LOCAL_STATE_FILE, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'nom', 'prix', 'image', 'galerie', 'categorie', 'description', 'couleur', 'taille']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in produits:
            p_copy = p.copy()
            p_copy['galerie'] = str(p_copy['galerie'])
            writer.writerow(p_copy)

PRODUITS = charger_produits()

CSS_STYLED = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; padding-bottom: 70px; }
    .header { background: linear-gradient(135deg, #2e1065 0%, #4c1d95 100%); color: white; padding: 18px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); flex-wrap: wrap; gap: 15px; }
    .brand-logo { font-size: 20px; font-weight: 800; color: white; text-decoration: none; display: flex; align-items: center; gap: 8px; }
    .search-form { display: flex; gap: 5px; flex-grow: 1; max-width: 350px; }
    .search-form input[type="text"] { width: 100%; padding: 8px 14px; border-radius: 6px; border: none; font-size: 14px; outline: none; }
    .search-form button { background: #ff9900; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; }
    .promo-banner { font-size: 14px; font-weight: 800; color: #ffffff; background: rgba(255, 255, 255, 0.1); padding: 6px 16px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.2); }
    .nav-actions { display: flex; align-items: center; gap: 15px; }
    .lang-select { background: #581c87; color: white; border: 1px solid #7c3aed; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .cart-btn { background: #e11d48; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px; }
    .cart-badge { background: white; color: #e11d48; border-radius: 50%; padding: 1px 7px; font-size: 12px; font-weight: 900; }
    .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
    .top-controls { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .cat-bar { display: flex; gap: 10px; flex-wrap: wrap; }
    .cat-tag { background: #e2e8f0; color: #334155; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-size: 13px; font-weight: 700; transition: all 0.2s; }
    .cat-tag:hover, .cat-tag.active { background: #6d28d9; color: white; }
    .sort-select { padding: 8px 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-weight: bold; background: #f8fafc; color: #334155; cursor: pointer; }
    .sec-header { font-size: 20px; font-weight: 800; color: #2e1065; margin: 35px 0 15px 0; border-bottom: 2px solid #e9d5ff; padding-bottom: 8px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
    .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); display: flex; flex-direction: column; border: 1px solid #f3f4f6; }
    .card-img-wrap { height: 190px; overflow: hidden; background: #f8fafc; display: block; }
    .card-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
    .card-body { padding: 15px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between; }
    .card-title { font-size: 13px; font-weight: 700; color: #1f2937; margin-bottom: 10px; text-decoration: none; height: 40px; overflow: hidden; display: block; }
    .card-price { font-size: 18px; font-weight: 900; color: #2563eb; margin-bottom: 8px; }
    .variant-badge { font-size: 11px; background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 4px; margin-bottom: 10px; display: inline-block; font-weight: 600; }
    .btn-buy { background: #6d28d9; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; text-decoration: none; text-align: center; display: block; width: 100%; }
    .btn-buy:hover { background: #581c87; }
    .btn-paypal { background: #0070ba; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; text-decoration: none; text-align: center; display: block; width: 100%; margin-bottom: 10px; }
    .btn-stripe { background: #635bff; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; text-decoration: none; text-align: center; display: block; width: 100%; }
    .logistic-box { background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px 15px; border-radius: 8px; margin: 15px 0; font-size: 12px; color: #1e40af; line-height: 1.5; font-weight: 600; }
    .floating-cart-bar { position: fixed; bottom: 0; left: 0; width: 100%; background: #1e1b4b; color: white; padding: 12px 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 20px rgba(0,0,0,0.3); z-index: 1000; font-weight: bold; }
    .floating-cart-bar a { background: #e11d48; color: white; padding: 8px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; }
    .pagination { display: flex; justify-content: center; gap: 8px; margin: 40px 0; }
    .pagination a, .pagination span { padding: 8px 14px; border-radius: 6px; font-weight: bold; text-decoration: none; font-size: 14px; border: 1px solid #cbd5e1; }
    .pagination a { background: white; color: #4c1d95; }
    .pagination .current { background: #6d28d9; color: white; border-color: #6d28d9; }
    .product-desc img { max-width: 100% !important; height: auto !important; display: block; margin: 10px auto; border-radius: 6px; }
</style>
"""

FLOATING_CART_SNIPPET = """
{% set cart_items = session.get('cart', []) %}
{% if cart_items %}
<div class="floating-cart-bar">
    <div>🛒 Mon Panier : {{ cart_items|length }} article(s) | Total : 
        {% set ns = namespace(total=0) %}
        {% for it in cart_items %}{% set ns.total = ns.total + it.prix|float %}{% endfor %}
        <strong>{{ "%.2f"|format(ns.total) }} €</strong>
    </div>
    <div>
        <a href="/cart?lang={{ lang }}">Voir le Panier / Valider ➡️</a>
    </div>
</div>
{% endif %}
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>Mon Shop Direct - Belgique</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <form action="/" method="GET" class="search-form">
            <input type="hidden" name="lang" value="{{ lang }}">
            {% if active_cat %}<input type="hidden" name="cat" value="{{ active_cat }}">{% endif %}
            {% if current_sort %}<input type="hidden" name="sort" value="{{ current_sort }}">{% endif %}
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
    <div class="container">
        <div class="top-controls">
            <div class="cat-bar">
                <a href="/?lang={{ lang }}{% if search_query %}&q={{ search_query }}{% endif %}{% if current_sort %}&sort={{ current_sort }}{% endif %}" class="cat-tag {% if not active_cat %}active{% endif %}">🔥 {{ t.all }}</a>
                {% for slug, nom in categories.items() %}
                <a href="/?cat={{ slug }}&lang={{ lang }}{% if search_query %}&q={{ search_query }}{% endif %}{% if current_sort %}&sort={{ current_sort }}{% endif %}" class="cat-tag {% if active_cat == slug %}active{% endif %}">{{ nom }}</a>
                {% endfor %}
            </div>
            <form action="/" method="GET" style="margin:0;">
                {% if active_cat %}<input type="hidden" name="cat" value="{{ active_cat }}">{% endif %}
                {% if search_query %}<input type="hidden" name="q" value="{{ search_query }}">{% endif %}
                <input type="hidden" name="lang" value="{{ lang }}">
                <select name="sort" class="sort-select" onchange="this.form.submit()">
                    <option value="default" {% if current_sort == 'default' %}selected{% endif %}>⚡ Pertinence</option>
                    <option value="price_asc" {% if current_sort == 'price_asc' %}selected{% endif %}>💶 Prix : Moins cher au plus cher</option>
                    <option value="price_desc" {% if current_sort == 'price_desc' %}selected{% endif %}>💎 Prix : Plus cher au moins cher</option>
                    <option value="new" {% if current_sort == 'new' %}selected{% endif %}>🚀 Nouveautés</option>
                </select>
            </form>
        </div>

        <div class="sec-header">🚀 Catalogue Direct {% if active_cat %}- {{ categories.get(active_cat, '') }}{% endif %} ({{ total_count }} articles)</div>
        <div class="grid">
            {% for p in produits %}
            <div class="card">
                <a href="/product/{{ p.id }}?lang={{ lang }}" class="card-img-wrap"><img src="{{ p.image }}" alt=""></a>
                <div class="card-body">
                    <a href="/product/{{ p.id }}?lang={{ lang }}" class="card-title">{{ p.nom }}</a>
                    <div>
                        <div class="card-price">{{ p.prix }} €</div>
                        <div class="variant-badge">🎨 {{ p.couleur }} | 📏 {{ p.taille }}</div>
                    </div>
                    <form action="/add/{{ p.id }}?lang={{ lang }}" method="POST"><button type="submit" class="btn-buy">{{ t.buy }}</button></form>
                </div>
            </div>
            {% endfor %}
        </div>
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page > 1 %}<a href="/?page={{ page - 1 }}{% if active_cat %}&cat={{ active_cat }}{% endif %}{% if search_query %}&q={{ search_query }}{% endif %}{% if current_sort %}&sort={{ current_sort }}{% endif %}&lang={{ lang }}">« Précédent</a>{% endif %}
            {% for p_num in range(1, total_pages + 1) %}
                {% if p_num == page %}<span class="current">{{ p_num }}</span>
                {% elif p_num <= 3 or p_num >= total_pages - 2 or (p_num >= page - 2 and p_num <= page + 2) %}
                <a href="/?page={{ p_num }}{% if active_cat %}&cat={{ active_cat }}{% endif %}{% if search_query %}&q={{ search_query }}{% endif %}{% if current_sort %}&sort={{ current_sort }}{% endif %}&lang={{ lang }}">{{ p_num }}</a>
                {% elif p_num == 4 or p_num == total_pages - 3 %}<span>...</span>{% endif %}
            {% endfor %}
            {% if page < total_pages %}<a href="/?page={{ page + 1 }}{% if active_cat %}&cat={{ active_cat }}{% endif %}{% if search_query %}&q={{ search_query }}{% endif %}{% if current_sort %}&sort={{ current_sort }}{% endif %}&lang={{ lang }}">Suivant »</a>{% endif %}
        </div>
        {% endif %}
    </div>
    """ + FLOATING_CART_SNIPPET + """
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
                <img src="{{ p.image }}" id="mainImg" style="width: 100%; max-height: 380px; object-fit: contain; border-radius: 8px; background: #f8fafc;">
                <div style="display: flex; gap: 10px; margin-top: 15px; overflow-x: auto;">
                    {% for img in p.galerie %}
                    <img src="{{ img }}" style="width: 70px; height: 70px; object-fit: cover; border-radius: 6px; cursor: pointer;" onclick="document.getElementById('mainImg').src = this.src">
                    {% endfor %}
                </div>
            </div>
            <div>
                <h1 style="font-size: 22px; font-weight: 800; margin-bottom: 12px;">{{ p.nom }}</h1>
                <div style="font-size: 28px; font-weight: 900; color: #2563eb; margin-bottom: 15px;">{{ p.prix }} €</div>
                
                <div style="margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #475569;">
                    <span>Option couleur : <span style="color:#6d28d9;">{{ p.couleur }}</span></span> &nbsp;|&nbsp; 
                    <span>Taille/Format : <span style="color:#6d28d9;">{{ p.taille }}</span></span>
                </div>

                <div class="logistic-box">
                    🚚 <strong>Transparence Logistique Belgique (Bpost / Mondial Relay) :</strong> Expédition express suivie depuis nos entrepôts partenaires. Livraison estimée entre <strong>3 à 6 jours ouvrés</strong> à votre domicile ou point relais en Belgique. Zéro frais de douane cachés.
                </div>

                <div class="product-desc" style="color: #4b5563; font-size: 13px; line-height: 1.6; margin-bottom: 25px;">{{ p.description | safe }}</div>
                <form action="/add/{{ p.id }}?lang={{ lang }}" method="POST"><button type="submit" class="btn-buy" style="padding: 14px; font-size: 16px;">{{ t.buy }}</button></form>
            </div>
        </div>
    </div>
    """ + FLOATING_CART_SNIPPET + """
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
                    <div style="flex-grow:1; margin-left: 20px;">
                        <div style="font-weight:700; font-size:14px;">{{ item.nom }}</div>
                        <div style="font-size:11px; color:#64748b; margin-top:3px;">{{ item.couleur }} / {{ item.taille }}</div>
                    </div>
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
    """ + FLOATING_CART_SNIPPET + """
</body>
</html>
"""

HTML_CHECKOUT = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Validation Commande</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/" class="brand-logo">🛍️ Mon Shop Direct</a>
        <a href="/cart" style="color:white; text-decoration:none; font-weight:bold;">⬅️ Panier</a>
    </div>
    <div class="container" style="max-width: 650px;">
        <div style="background:white; border-radius: 12px; padding: 30px;">
            <h2 style="color: #2e1065; margin-bottom: 20px;">💳 Paiement Sécurisé Officiel</h2>
            <form action="/process_order" method="POST">
                <div style="margin-bottom: 15px;"><label style="display:block; font-weight:bold; margin-bottom:5px;">Nom et Prénom</label><input type="text" name="nom" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <div style="margin-bottom: 15px;"><label style="display:block; font-weight:bold; margin-bottom:5px;">Adresse postale (Belgique)</label><input type="text" name="adresse" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;">
                    <div><label style="display:block; font-weight:bold; margin-bottom:5px;">Code Postal</label><input type="text" name="cp" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                    <div><label style="display:block; font-weight:bold; margin-bottom:5px;">Ville</label><input type="text" name="ville" required style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;"></div>
                </div>
                <button type="submit" name="gateway" value="paypal" class="btn-paypal">🅿️ Payer avec PayPal (Officiel)</button>
                <button type="submit" name="gateway" value="stripe" class="btn-stripe">💳 Payer avec Stripe (Carte bancaire - Live 2FA)</button>
            </form>
        </div>
    </div>
    """ + FLOATING_CART_SNIPPET + """
</body>
</html>
"""

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Commande Validée</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header"><a href="/" class="brand-logo">🛍️ Mon Shop Direct</a></div>
    <div class="container" style="max-width: 750px;">
        <div style="background:white; border-radius: 12px; padding: 40px; text-align: center;">
            <h2 style="color: #16a34a; font-size: 26px; margin-bottom: 10px;">Paiement officiel validé avec succès !</h2>
            <p style="color: #4b5563; margin-bottom: 20px;">Votre commande a bien été enregistrée et transmise à notre service logistique pour une livraison rapide en Belgique.</p>
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
            <form action="/admin/login" method="POST">
                <input type="password" name="password" required placeholder="Mot de passe admin" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 15px;">
                <button type="submit" style="width: 100%; background: #6d28d9; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer;">Se connecter</button>
            </form>
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
            <a href="/admin/logout" style="color:#fca5a5; text-decoration:none; font-weight:bold;">Déconnexion 🚪</a>
        </div>
    </div>
    <div class="container">
        <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
            <h3 style="color: #2e1065; margin-bottom: 10px;">📂 Importer un fichier CSV (Nettoyage & Remplacement Propre)</h3>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    lang = request.args.get('lang', 'fr')
    if lang not in TRADUCTIONS:
        lang = 'fr'
    t = TRADUCTIONS[lang]
    
    cat = request.args.get('cat', '')
    sort = request.args.get('sort', 'default')
    q = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 16

    liste = PRODUITS
    if cat:
        liste = [p for p in liste if p.get('categorie') == cat]
    if q:
        liste = [p for p in liste if q in p.get('nom', '').lower() or q in p.get('description', '').lower()]

    if sort == 'price_asc':
        liste = sorted(liste, key=lambda x: float(x.get('prix', 0)))
    elif sort == 'price_desc':
        liste = sorted(liste, key=lambda x: float(x.get('prix', 0)), reverse=True)
    elif sort == 'new':
        liste = sorted(liste, key=lambda x: x.get('id', 0), reverse=True)

    total_count = len(liste)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    
    debut = (page - 1) * per_page
    fin = debut + per_page
    produits_page = liste[debut:fin]

    return render_template_string(
        HTML_INDEX, 
        produits=produits_page, 
        t=t, 
        lang=lang, 
        categories=CATEGORIES, 
        active_cat=cat, 
        current_sort=sort, 
        search_query=q, 
        page=page, 
        total_pages=total_pages, 
        total_count=total_count
    )

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    lang = request.args.get('lang', 'fr')
    if lang not in TRADUCTIONS: lang = 'fr'
    t = TRADUCTIONS[lang]
    
    p = next((item for item in PRODUITS if item["id"] == product_id), None)
    if not p:
        return redirect(url_for('index', lang=lang))
    
    return render_template_string(HTML_PRODUCT, p=p, t=t, lang=lang)

@app.route("/add/<int:product_id>", methods=['POST'])
def add_to_cart(product_id):
    lang = request.args.get('lang', 'fr')
    p = next((item for item in PRODUITS if item["id"] == product_id), None)
    if p:
        cart = session.get('cart', [])
        cart.append(p)
        session['cart'] = cart
    return redirect(request.referrer or url_for('index', lang=lang))

@app.route("/remove/<int:index>")
def remove_from_cart(index):
    lang = request.args.get('lang', 'fr')
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    return redirect(url_for('view_cart', lang=lang))

@app.route("/cart")
def view_cart():
    lang = request.args.get('lang', 'fr')
    if lang not in TRADUCTIONS: lang = 'fr'
    t = TRADUCTIONS[lang]
    cart = session.get('cart', [])
    total = sum(float(item['prix']) for item in cart)
    return render_template_string(HTML_CART, cart=cart, total=total, t=t, lang=lang)

@app.route("/clear")
def clear_cart():
    lang = request.args.get('lang', 'fr')
    session.pop('cart', None)
    return redirect(url_for('view_cart', lang=lang))

@app.route("/checkout")
def checkout():
    return render_template_string(HTML_CHECKOUT)

@app.route("/process_order", methods=['POST'])
def process_order():
    session.pop('cart', None)
    return render_template_string(HTML_SUCCESS)

@app.route("/set_lang", methods=['POST'])
def set_lang():
    lang = request.form.get('lang', 'fr')
    return redirect(url_for('index', lang=lang))

@app.route("/admin")
def admin_panel():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login'))
    return render_template_string(HTML_ADMIN)

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect(url_for('admin_panel'))
    return render_template_string(HTML_LOGIN)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)