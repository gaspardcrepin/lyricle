import os
import psycopg2
from dotenv import load_dotenv

# Charge les variables de ton .env (qui pointent maintenant vers Azure)
load_dotenv(dotenv_path='../.env')

def init_database():
    print("Connexion à Azure PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"), # Doit être "postgres"
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        print("Création de la table 'songs'...")
        
        # Le SQL de création (avec la colonne snippets en tableau TEXT[])
        create_table_sql = """
        DROP TABLE IF EXISTS songs;

        CREATE TABLE songs (
            id SERIAL PRIMARY KEY,
            artist VARCHAR(100) NOT NULL,
            title VARCHAR(100) NOT NULL,
            snippets TEXT[] NOT NULL,     -- Tableau de textes pour les indices
            year INT NOT NULL,
            country VARCHAR(50) NOT NULL,
            genre VARCHAR(50) NOT NULL,
            streams INT NOT NULL,
            UNIQUE(artist, title)
        );
        """
        
        cur.execute(create_table_sql)
        conn.commit()
        
        print("Table créée avec succès sur Azure !")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    init_database()