import os
import datetime
import psycopg2
import random
from flask import Flask, render_template, request, jsonify, session
import re

app = Flask(__name__)
app.secret_key = "secret_key_dev"

def get_random_song():
    conn = get_db_connection()
    cur = conn.cursor()
    # RANDOM() est spécifique à PostgreSQL
    cur.execute('SELECT * FROM songs ORDER BY RANDOM() LIMIT 1;') 
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row: return None
    
    return {
        "id": row[0], "artist": row[1], "title": row[2], 
        "snippets": row[3], "year": row[4], "country": row[5], 
        "genre": row[6], "streams": row[7]
    }


@app.route('/api/start_unlimited')
def start_unlimited():
    song = get_random_song()
    if not song:
        return jsonify({"error": "Pas de chansons"}), 500
    
    # On sauvegarde l'ID de la chanson mystère dans la session de l'utilisateur
    session['unlimited_song_id'] = song['id']
    
    # On renvoie juste le premier snippet pour commencer
    return jsonify({
        "snippet": song['snippets'][0] if song['snippets'] else "...",
        "message": "Nouvelle partie lancée !"
    })

# --- 1. Connexion Base de Données ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD']
        )
        return conn
    except Exception as e:
        print(f"Erreur connexion DB: {e}")
        return None

# --- 2. Récupération de la chanson du jour ---
def get_daily_song():
    conn = get_db_connection()
    if not conn: return None
    cur = conn.cursor()
    
    # On récupère toutes les chansons triées par ID pour garder un ordre constant
    cur.execute('SELECT * FROM songs ORDER BY id;')
    songs = cur.fetchall()
    
    if not songs:
        return None

    # On choisit la chanson du jour selon la date
    today_index = datetime.date.today().toordinal() % len(songs)
    row = songs[today_index]
    
    # Mapping des colonnes (Attention à l'ordre dans ta BDD)
    # id(0), artist(1), title(2), snippets(3), year(4), country(5), genre(6), streams(7)
    daily_song = {
        "id": row[0], 
        "artist": row[1], 
        "title": row[2], 
        "snippets": row[3], # C'est maintenant une LISTE (Array PostgreSQL)
        "year": row[4], 
        "country": row[5], 
        "genre": row[6], 
        "streams": row[7]
    }
    cur.close()
    conn.close()
    return daily_song

# --- 3. Route Accueil ---
@app.route('/')
def home():
    song = get_daily_song()
    if not song:
        return "Erreur critique : Aucune chanson en base (lancez ingest.py)."
    
    # Au premier chargement, on affiche juste la 1ère phrase
    # (Ou "..." si la liste est vide par sécurité)
    first_snippet = song['snippets'][0] if song['snippets'] else "..."
    
    return render_template('index.html', snippet=first_snippet)

# --- 4. Route Recherche (Autocomplétion) ---
@app.route('/api/search')
def search_songs():
    query = request.args.get('q', '').lower()
    if len(query) < 2: return jsonify([])

    conn = get_db_connection()
    cur = conn.cursor()
    # Recherche insensible à la casse dans titre ou artiste
    sql = """
        SELECT title, artist 
        FROM songs 
        WHERE title ILIKE %s OR artist ILIKE %s 
        LIMIT 5
    """
    search_term = f'%{query}%'
    cur.execute(sql, (search_term, search_term))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{'title': r[0], 'artist': r[1]} for r in results])

# --- 5. Route Guess (Le Cœur du Jeu) ---
@app.route('/api/guess', methods=['POST'])
def check_guess():
    # 1. Récupération des données envoyées par le JS
    data = request.json
    guess_title = data.get('title')
    mode = data.get('mode', 'daily') # Par défaut 'daily' si non précisé
    
    target = None
    
    # 2. DÉTERMINATION DE LA CIBLE (TARGET)
    conn = get_db_connection()
    cur = conn.cursor()

    if mode == 'daily':
        # Mode Classique : On appelle ta fonction existante
        target = get_daily_song()
        
    elif mode == 'unlimited':
        # Mode Arcade : On récupère l'ID stocké dans la session de l'utilisateur
        target_id = session.get('unlimited_song_id')
        
        if not target_id:
            cur.close()
            conn.close()
            return jsonify({"error": "Aucune partie illimitée lancée. Appelez /api/start_unlimited d'abord."}), 400
            
        # On va chercher les infos de cet ID spécifique
        cur.execute("SELECT * FROM songs WHERE id = %s", (target_id,))
        row = cur.fetchone()
        
        if row:
            # On transforme le tuple BDD en dictionnaire propre
            target = {
                "id": row[0], 
                "artist": row[1], 
                "title": row[2], 
                "snippets": row[3], # TEXT[] -> Liste Python
                "year": row[4], 
                "country": row[5], 
                "genre": row[6], 
                "streams": row[7]
            }

    # Sécurité si la cible n'est pas trouvée (bug BDD ou session expirée)
    if not target:
        cur.close()
        conn.close()
        return jsonify({"error": "Impossible de récupérer la chanson cible"}), 500

    # 3. RÉCUPÉRATION DE LA PROPOSITION DU JOUEUR (GUESS)
    cur.execute("SELECT * FROM songs WHERE title = %s", (guess_title,))
    row_guess = cur.fetchone()
    
    cur.close()
    conn.close()

    if not row_guess:
        return jsonify({"error": "Cette chanson n'existe pas dans la base de données"}), 404

    # Mapping de la proposition
    guessed = {
        "artist": row_guess[1], 
        "title": row_guess[2], 
        "year": row_guess[4], 
        "country": row_guess[5], 
        "genre": row_guess[6], 
        "streams": row_guess[7]
    }

    def clean_str(s):
        if not s: return ""
        t = s.lower()
        # Enlever parenthèses (...) ou crochets [...]
        t = re.sub(r"\(.*?\)", "", t)
        t = re.sub(r"\[.*?\]", "", t)
        # Enlever après un tiret (ex: " - Remastered 2022")
        t = t.split('-')[0]
        # Enlever la ponctuation inutile
        t = re.sub(r"[^a-z0-9\s]", "", t)
        # Enlever les espaces multiples et les espaces au début/fin
        return t.strip()

    # On compare les versions propres
    target_clean = clean_str(target['title'])
    guess_clean = clean_str(guessed['title'])

    # 4. COMPARAISON ET CONSTRUCTION DE LA RÉPONSE JSON
    is_correct = (guess_clean == target_clean)

    result = {
        "is_correct": is_correct,
        "title": guessed['title'],
        
        # INDISPENSABLE : On renvoie la liste des paroles pour l'affichage progressif
        "snippets": target['snippets'], 
        
        # Comparaison Artiste
        "artist": { 
            "value": guessed['artist'], 
            "status": "correct" if guessed['artist'] == target['artist'] else "wrong" 
        },
        
        # Comparaison Genre
        "genre": { 
            "value": guessed['genre'], 
            "status": "correct" if guessed['genre'] == target['genre'] else "wrong" 
        },
        
        # Comparaison Pays
        "country": { 
            "value": guessed['country'], 
            "status": "correct" if guessed['country'] == target['country'] else "wrong" 
        },
        
        # Comparaison Année (avec Flèches)
        "year": {
            "value": guessed['year'],
            "status": "correct" if guessed['year'] == target['year'] else "wrong",
            "direction": "up" if target['year'] > guessed['year'] else ("down" if target['year'] < guessed['year'] else "equal")
        },
        
        # Comparaison Streams (avec Flèches)
        "streams": {
            "value": f"{guessed['streams']}M", # Ajout du 'M' pour l'affichage
            "status": "correct" if guessed['streams'] == target['streams'] else "wrong",
            "direction": "up" if target['streams'] > guessed['streams'] else ("down" if target['streams'] < guessed['streams'] else "equal")
        }
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)