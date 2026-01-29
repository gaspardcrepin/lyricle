import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

print("--- TEST CONNEXION ---")

# 1. Utilisation d'une Session pour ignorer les proxies
session = requests.Session()
session.trust_env = False  # C'est la commande pour ignorer les proxies système

# 2. Authentification sur l'URL OFFICIELLE
auth_url = 'https://accounts.spotify.com/api/token'
auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

try:
    print(f"1. POST vers {auth_url}")
    
    response = session.post(
        auth_url,
        data={'grant_type': 'client_credentials'},
        headers={'Authorization': f'Basic {auth_header}'},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Erreur: {response.text}")
        exit()
        
    token = response.json()['access_token']
    print("   Token obtenu.")

    # 3. Récupération Playlist sur l'URL OFFICIELLE
    playlist_id = "0slE73JFtRr3F2KnfoWlbO"
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    
    print(f"2. GET vers {playlist_url}")
    
    resp = session.get(
        playlist_url, 
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Succès. Playlist: {data['name']}")
    else:
        print(f"   Erreur API: {resp.status_code}")
        print(resp.text)

except Exception as e:
    print(f"   Exception: {e}")