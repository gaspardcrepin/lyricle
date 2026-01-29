import os
import time
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.cache_handler import MemoryCacheHandler
import lyricsgenius
import requests
import psycopg2
from dotenv import load_dotenv

# 1. Chargement Env
load_dotenv(dotenv_path='../.env')

# 2. FIX RÉSEAU : Session qui ignore les proxys (Anti-GoogleUserContent)
session = requests.Session()
session.trust_env = False 

# 3. Config Spotify
auth_manager = SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    cache_handler=MemoryCacheHandler()
)
sp = spotipy.Spotify(auth_manager=auth_manager, requests_session=session, requests_timeout=10)

# 4. Config Genius
genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"))
genius.verbose = False    
genius.remove_section_headers = True 

# --- FONCTIONS BDD & UTILS ---

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

def get_artist_country(artist_name):
    # Tes 5 artistes ont des villes fixes
    mapping = {
        "Kendrick Lamar": "USA (Compton)",
        "Drake": "Canada (Toronto)",
        "Kanye West": "USA (Chicago)",
        "Future": "USA (Atlanta)",
        "PARTYNEXTDOOR": "Canada (Mississauga)",
        "PartyNextDoor": "Canada (Mississauga)"
    }
    # Recherche partielle (ex: "Drake" marche pour "Drake")
    for key, val in mapping.items():
        if key.lower() in artist_name.lower():
            return val
    return "USA" # Fallback par défaut pour le Rap US

def simplify_genre(spotify_genres):
    if not spotify_genres: return "Rap"
    detailed = [g.title() for g in spotify_genres[:2]]
    return " / ".join(detailed)

def get_snippets_list(lyrics):
    # Nettoyage
    lines = [l.strip() for l in lyrics.split('\n') 
             if l.strip() and "[" not in l and "Lyrics" not in l and len(l.strip()) > 10]
    
    if len(lines) > 8:
        start = random.randint(0, len(lines) - 7)
        return lines[start : start + 6]
    
    # Padding si trop court
    res = lines[:6]
    while len(res) < 6:
        res.append("...")
    return res

# --- NOUVELLE LOGIQUE D'INGESTION ---

def ingest_artist_catalog(target_artist_name):
    print(f"\n🎤 Recherche de l'artiste : {target_artist_name}...")
    
    # 1. Trouver l'ID de l'artiste
    search = sp.search(q=target_artist_name, type='artist', limit=1)
    if not search['artists']['items']:
        print("❌ Artiste introuvable.")
        return

    artist_obj = search['artists']['items'][0]
    artist_id = artist_obj['id']
    print(f"   -> ID trouvé : {artist_id} ({artist_obj['name']})")
    
    # 2. Récupérer les Top Tracks (Les 10 hits incontournables)
    print("   -> Récupération des Top Tracks...")
    top_tracks = sp.artist_top_tracks(artist_id)['tracks']
    
    # 3. Récupérer aussi quelques albums récents pour avoir plus de choix
    # On prend les 5 derniers albums pour avoir des "Deep cuts"
    albums = sp.artist_albums(artist_id, album_type='album', limit=5)['items']
    
    all_tracks_to_process = top_tracks
    
    for alb in albums:
        # On ajoute les tracks des albums à la liste
        try:
            alb_tracks = sp.album_tracks(alb['id'])['items']
            # On ajoute le champ 'album' manquant dans les tracks d'album
            for t in alb_tracks:
                t['album'] = alb # On injecte l'objet album parent
            all_tracks_to_process.extend(alb_tracks)
        except:
            pass

    print(f"   -> {len(all_tracks_to_process)} titres potentiels identifiés.")
    
    conn = get_db_connection()
    cur = conn.cursor()
    count = 0
    processed_titles = set() # Pour éviter les doublons (ex: Top Track aussi dans Album)

    for track in all_tracks_to_process:
        title = track['name'].split(" - ")[0].split(" (")[0]
        
        # Filtre doublon script
        if title in processed_titles: continue
        processed_titles.add(title)
        
        # Filtre doublon BDD
        cur.execute("SELECT id FROM songs WHERE title = %s", (title,))
        if cur.fetchone():
            print(f"⏩ Déjà en base : {title}")
            continue
            
        # On filtre pour ne prendre que ceux où l'artiste cible est le PRINCIPAL
        # (Pour éviter d'importer une chanson de Travis Scott où Drake est juste en feat)
        main_artist = track['artists'][0]['name']
        if target_artist_name.lower() not in main_artist.lower():
            # Si c'est un featuring, on le prend quand même mais on note le main artist
            pass 

        print(f"📥 Traitement : {title}")
        
        try:
            # Récupération Infos
            if 'album' in track:
                r_date = track['album'].get('release_date', '2020-01-01')
            else:
                # Si Top Track, l'album est inclus, sinon fallback
                r_date = '2024-01-01'
            
            year = int(r_date.split("-")[0])
            pop = track.get('popularity', 60)
            streams = int((pop ** 2.6) / 100) + random.randint(1, 99)
            
            genre = simplify_genre(sp.artist(track['artists'][0]['id'])['genres'])
            country = get_artist_country(target_artist_name) # On force le pays de la cible
            
            # Genius
            # Astuce : On cherche "Titre Artiste" pour aider Genius
            search_query = f"{title} {target_artist_name}"
            song_genius = genius.search_song(title, target_artist_name)
            
            if song_genius:
                snippets = get_snippets_list(song_genius.lyrics)
                
                # Le nom de l'artiste affiché sera le Main Artist de la track
                # (ex: Si c'est "Poetic Justice", l'artiste reste Kendrick)
                cur.execute("""
                    INSERT INTO songs (artist, title, snippets, year, country, genre, streams)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (main_artist, title, snippets, year, country, genre, streams))
                conn.commit()
                print(f"✅ Ajouté !")
                count += 1
            else:
                print("❌ Pas de paroles.")

        except Exception as e:
            print(f"🔥 Erreur : {e}")
            conn.rollback()
            
    cur.close()
    conn.close()
    print(f"✨ Fini pour {target_artist_name} : {count} ajouts.\n")

# --- LANCEMENT ---
if __name__ == "__main__":
    # Liste des noms (plus besoin d'IDs !)
    TARGETS = [
        "Kendrick Lamar",
        "Drake",
        "Future",
        "Kanye West",
        "PARTYNEXTDOOR"
    ]
    
    for artist in TARGETS:
        ingest_artist_catalog(artist)