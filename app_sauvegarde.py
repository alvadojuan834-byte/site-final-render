from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = 'cle_secrete_boutique_v8'

TRADUCTIONS = {
    "fr": {"shop": "MonShop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Panier", "admin": "Admin", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide.", "color": "Couleur", "size": "Taille", "desc": "Description du produit"},
    "be": {"shop": "MonShop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Panier", "admin": "Admin", "all": "Toutes les catégories", "buy": "Acheter", "total": "Total", "checkout": "🔒 Valider la commande", "empty": "Votre panier est vide wesh.", "color": "Couleur", "size": "Taille", "desc": "Description du produit"},
    "en": {"shop": "MonShop Direct", "promo": "🔥 AliExpress Boost Promos 🔥", "cart": "Cart", "admin": "Admin", "all": "All categories", "buy": "Buy Now", "total": "Total", "checkout": "🔒 Checkout", "empty": "Your cart is empty.", "color": "Color", "size": "Size", "desc": "Product description"},
    "de": {"shop": "MonShop Direct", "promo": "🔥 AliExpress Boost Angebote 🔥", "cart": "Warenkorb", "admin": "Admin", "all": "Alle Kategorien", "buy": "Kaufen", "total": "Gesamt", "checkout": "🔒 Zur Kasse", "empty": "Ihr Warenkorb ist leer.", "color": "Farbe", "size": "Größe", "desc": "Produktbeschreibung"},
    "es": {"shop": "MonShop Direct", "promo": "🔥 Promos Boost AliExpress 🔥", "cart": "Carrito", "admin": "Admin", "all": "Todas las categorías", "buy": "Comprar", "total": "Total", "checkout": "🔒 Tramitar pedido", "empty": "Tu carrito está vacío.", "color": "Color", "size": "Talla", "desc": "Descripción del producto"},
    "nl": {"shop": "MonShop Direct", "promo": "🔥 AliExpress Boost Promo's 🔥", "cart": "Winkelmand", "admin": "Admin", "all": "Alle categorieën", "buy": "Kopen", "total": "Totaal", "checkout": "🔒 Afrekenen", "empty": "Je winkelmand is leeg.", "color": "Kleur", "size": "Maat", "desc": "Produktbeschrijving"}
}

# Fonction d'importation automatique des CSV AliExpress
def charger_produits_aliexpress():
    produits_importes = []
    dossier_csv = r"C:\csv.aliexpress"
    
    if not os.path.exists(dossier_csv):
        # Fallback si le dossier n'est pas trouvé, on met un produit par défaut
        return [{
            "id": 0, "nom": "Radiateur Électrique à Convection 2000W", "prix": "49.99",
            "image": "https://images.unsplash.com/photo-1585338107529-13afc5f02586?w=500",
            "galerie": ["https://images.unsplash.com/photo-1585338107529-13afc5f02586?w=500"],
            "categorie": "Électroménager", "couleurs": ["Blanc", "Noir"], "description": "Description par défaut."
        }]

    c = 0
    for fichier in os.listdir(dossier_csv):
        if fichier.endswith(".csv"):
            chemin_complet = os.path.join(dossier_csv, fichier)
            try:
                with open(chemin_complet, mode='r', encoding='utf-8-sig') as f:
                    lecteur = csv.DictReader(f)
                    for ligne in lecteur:
                        nom = ligne.get('Title', 'Produit AliExpress')
                        prix = ligne.get('Sale price', '19.99')
                        if not prix:
                            prix = '19.99'
                        image = ligne.get('Product Image Url', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500')
                        
                        # Nettoyage de l'URL de l'image principale si elle contient plusieurs liens séparés par des virgules
                        if ',' in image:
                            image = image.split(',')[0].strip()

                        galerie_raw = ligne.get('Main images url', '')
                        galerie = [img.strip() for img in galerie_raw.split(',') if img.strip()]
                        if not galerie:
                            galerie = [image]

                        desc = ligne.get('Product description html', 'Aucune description disponible.')

                        produits_importes.append({
                            "id": c,
                            "nom": nom,
                            "prix": prix,
                            "image": image,
                            "galerie": galerie[:5], # Limiter à 5 images max pour la galerie
                            "categorie": "AliExpress Store",
                            "couleurs": ["Standard"],
                            "description": desc[:300] + "..." # Version courte propre pour l'affichage
                        })
                        c += 1
            except Exception as e:
                print(f"Erreur lecture {fichier}: {e}")
                
    if not produits_importes:
        produits_importes.append({
            "id": 0, "nom": "Produit Test", "prix": "10.00",
            "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500",
            "galerie": ["https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"],
            "categorie": "Général", "couleurs": ["Standard"], "description": "Test"
        })
        
    return produits_importes

PRODUITS = charger_produits_aliexpress()
COMMANDES = []

CSS_STYLED = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; }
    .header { background: linear-gradient(135deg, #2e1065 0%, #4c1d95 100%); color: white; padding: 18px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .brand-logo { font-size: 20px; font-weight: 800; color: white; text-decoration: none; display: flex; align-items: center; gap: 8px; }
    .promo-banner { font-size: 17px; font-weight: 800; color: #ffffff; background: rgba(255, 255, 255, 0.1); padding: 8px 20px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.2); }
    .nav-actions { display: flex; align-items: center; gap: 15px; }
    .lang-select { background: #581c87; color: white; border: 1px solid #7c3aed; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .cart-btn { background: #e11d48; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px; }
    .cart-badge { background: white; color: #e11d48; border-radius: 50%; padding: 1px 7px; font-size: 12px; font-weight: 900; }
    .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
    .cat-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 30px; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
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
    .btn-buy:hover { background: #581c87; }
</style>
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>MonShop Direct</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <div class="promo-banner">{{ t.promo }} ({{ produits|length }} articles)</div>
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
            <a href="/admin?lang={{ lang }}" style="color: #c084fc; text-decoration: none; font-weight: bold; font-size: 13px;">⚙️ {{ t.admin }}</a>
        </div>
    </div>
    <div class="container">
        <div class="sec-header">🚀 Catalogue AliExpress Importé ({{ produits|length }} produits)</div>
        <div class="grid">
            {% for p in produits[:40] %}
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
        <div style="background: white; border-radius: 12px; padding: 30px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 20px;">
            <div>
                <img src="{{ p.image }}" id="mainImg" style="width: 100%; height: 380px; object-fit: cover; border-radius: 8px; border: 1px solid #e2e8f0;">
                <div style="display: flex; gap: 10px; margin-top: 15px; overflow-x: auto;">
                    {% for img in p.galerie %}
                    <img src="{{ img }}" style="width: 70px; height: 70px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 2px solid #cbd5e1;" onclick="document.getElementById('mainImg').src = this.src">
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
        <div style="background:white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
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
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>Validation Commande</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <div class="promo-banner">{{ t.promo }}</div>
        <a href="/cart?lang={{ lang }}" style="color:white; text-decoration:none; font-weight:bold;">⬅️ Panier</a>
    </div>
    <div class="container" style="max-width: 650px;">
        <div style="background:white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <h2 style="color: #2e1065; margin-bottom: 10px;">🔒 Tunnel de Paiement Sécurisé</h2>
            <p style="color: #64748b; font-size: 14px; margin-bottom: 25px;">Entrez vos coordonnées de livraison exactes pour acheminer la commande (prêt pour AliExpress).</p>
            <form action="/process_order?lang={{ lang }}" method="POST">
                <div style="margin-bottom: 15px;">
                    <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Nom et Prénom</label>
                    <input type="text" name="nom" required placeholder="Jean Dupont" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Adresse postale (Rue et numéro)</label>
                    <input type="text" name="adresse" required placeholder="123 Rue de la République" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                    <div>
                        <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Code Postal</label>
                        <input type="text" name="cp" required placeholder="75001" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                    </div>
                    <div>
                        <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Ville</label>
                        <input type="text" name="ville" required placeholder="Paris" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Pays</label>
                    <input type="text" name="pays" required placeholder="France / Belgique" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                </div>
                <div style="margin-bottom: 25px;">
                    <label style="display:block; font-weight:bold; margin-bottom:5px; font-size:13px;">Téléphone (pour le transporteur)</label>
                    <input type="tel" name="tel" required placeholder="0612345678" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:6px;">
                </div>
                <button type="submit" class="btn-buy" style="background:#16a34a; padding: 14px; font-size: 16px;">Confirmer et Payer ({{"%.2f"|format(total)}} €)</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>Commande Validée</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ {{ t.shop }}</a>
        <div class="promo-banner">{{ t.promo }}</div>
    </div>
    <div class="container" style="max-width: 750px;">
        <div style="background:white; border-radius: 12px; padding: 40px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <div style="font-size: 50px; margin-bottom: 15px;">🎉</div>
            <h2 style="color: #16a34a; font-size: 26px; margin-bottom: 10px;">Commande validée avec succès !</h2>
            <p style="color: #64748b; margin-bottom: 30px;">Merci <strong>{{ commande.nom }}</strong>. La commande a bien été enregistrée et transmise au système.</p>
            
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 30px;">
                <h4 style="color: #2e1065; margin-bottom: 10px;">📦 Fiche de réexpédition (Prêt pour AliExpress) :</h4>
                <p><strong>Destinataire :</strong> {{ commande.nom }}</p>
                <p><strong>Adresse :</strong> {{ commande.adresse }}, {{ commande.cp }} {{ commande.ville }} ({{ commande.pays }})</p>
                <p><strong>Téléphone :</strong> {{ commande.tel }}</p>
                <hr style="margin: 10px 0; border:0; border-top:1px solid #cbd5e1;">
                <p style="font-weight: bold;">Articles commandés :</p>
                <ul style="padding-left: 20px; font-size: 14px; color: #334155;">
                    {% for item in commande.items %}
                    <li>{{ item.nom }} - {{ item.prix }} €</li>
                    {% endfor %}
                </ul>
            </div>
            
            <a href="/?lang={{ lang }}" class="btn-buy" style="display:inline-block; width:auto; padding: 12px 30px;">Retourner à la boutique</a>
        </div>
    </div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head><meta charset="UTF-8"><title>Administration</title>""" + CSS_STYLED + """</head>
<body>
    <div class="header">
        <a href="/?lang={{ lang }}" class="brand-logo">🛍️ ADMIN SHOP</a>
        <div class="promo-banner">⚙️ Catalogue Total : {{ produits|length }} articles</div>
        <a href="/?lang={{ lang }}" style="color:white; text-decoration:none; font-weight:bold;">Voir le site ➡️</a>
    </div>
    <div class="container">
        <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h3 style="color: #2e1065; margin-bottom: 15px;">📦 Produits importés d'AliExpress</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr style="border-bottom: 2px solid #e2e8f0; text-align: left;"><th style="padding: 8px;">ID</th><th style="padding: 8px;">Nom</th><th style="padding: 8px;">Prix</th><th style="padding: 8px;">Action</th></tr>
                {% for p in produits[:50] %}
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 8px;">{{ p.id }}</td>
                    <td style="padding: 8px; font-weight: bold;">{{ p.nom }}</td>
                    <td style="padding: 8px;">{{ p.prix }} €</td>
                    <td style="padding: 8px;"><a href="/admin/delete/{{ p.id }}?lang={{ lang }}" style="color: #ef4444; font-weight: bold; text-decoration: none;">Supprimer</a></td>
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
    return render_template_string(HTML_INDEX, produits=PRODUITS, lang=lang, t=t)

@app.route('/product/<int:p_id>')
def product(p_id):
    lang = session.get('lang', 'fr')
    p = next((item for item in PRODUITS if item["id"] == p_id), None)
    if not p: return redirect(url_for('home'))
    t = TRADUCTIONS.get(lang, TRADUCTIONS['fr'])
    return render_template_string(HTML_PRODUCT, p=p, lang=lang, t=t)

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
    t = TRADUCTIONS.get(lang, TRADUCTIONS['fr'])
    return render_template_string(HTML_CART, cart=items, total=total, lang=lang, t=t)

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
    lang = request.args.get('lang', 'fr')
    items = session.get('cart', [])
    if not items: return redirect(url_for('home'))
    total = sum(float(item['prix']) for item in items if item['prix'].replace('.','',1).isdigit())
    t = TRADUCTIONS.get(lang, TRADUCTIONS['fr'])
    return render_template_string(HTML_CHECKOUT, total=total, lang=lang, t=t)

@app.route('/process_order', methods=['POST'])
def process_order():
    lang = request.args.get('lang', 'fr')
    items = session.get('cart', [])
    commande = {
        "nom": request.form.get('nom'),
        "adresse": request.form.get('adresse'),
        "cp": request.form.get('cp'),
        "ville": request.form.get('ville'),
        "pays": request.form.get('pays'),
        "tel": request.form.get('tel'),
        "items": items,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    COMMANDES.insert(0, commande)
    session.pop('cart', None)
    t = TRADUCTIONS.get(lang, TRADUCTIONS['fr'])
    return render_template_string(HTML_SUCCESS, commande=commande, lang=lang, t=t)

@app.route('/admin')
def admin():
    lang = request.args.get('lang', 'fr')
    return render_template_string(HTML_ADMIN, produits=PRODUITS, lang=lang)

@app.route('/admin/delete/<int:p_id>')
def admin_delete(p_id):
    global PRODUITS
    lang = request.args.get('lang', 'fr')
    PRODUITS = [p for p in PRODUITS if p['id'] != p_id]
    return redirect(url_for('admin', lang=lang))

if __name__ == '__main__':
    app.run(port=5050, debug=True)
