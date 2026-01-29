import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

def clean_database():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        print("🧹 Nettoyage des titres et artistes...")
        
        # 1. Enlever les espaces devant/derrière (TRIM)
        cur.execute("UPDATE songs SET title = TRIM(title);")
        cur.execute("UPDATE songs SET artist = TRIM(artist);")
        
        # 2. Correction spécifique pour N95 si l'artiste est faux
        # Si N95 est attribué à Travis Scott par erreur, on le supprime ou on le corrige
        cur.execute("SELECT artist FROM songs WHERE title = 'N95'")
        rows = cur.fetchall()
        for row in rows:
            print(f"⚠️ Trouvé N95 par : {row[0]}")
            if "Travis" in row[0]:
                print("   -> Suppression de l'entrée erronée Travis/N95")
                cur.execute("DELETE FROM songs WHERE title = 'N95' AND artist LIKE '%Travis%';")
        
        conn.commit()
        print("✨ Base de données propre !")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    clean_database()