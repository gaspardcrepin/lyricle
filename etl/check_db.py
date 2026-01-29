import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env') # Charge tes configs Azure depuis le .env

try:
    print(f"Connexion à {os.getenv('DB_HOST')}...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"), # Doit être 'postgres'
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM songs;")
    count = cur.fetchone()[0]
    
    print(f"📊 Nombre de chansons trouvées sur Azure : {count}")
    
    if count > 0:
        cur.execute("SELECT title FROM songs LIMIT 3;")
        print("Exemples :", cur.fetchall())
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Erreur de connexion : {e}")