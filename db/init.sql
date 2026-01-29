DROP TABLE IF EXISTS songs;

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    artist VARCHAR(100) NOT NULL,
    title VARCHAR(100) NOT NULL,
    snippets TEXT[] NOT NULL,
    year INT NOT NULL,           -- Année de sortie
    country VARCHAR(50) NOT NULL,-- Pays de l'artiste
    genre VARCHAR(50) NOT NULL,  -- Style principal
    streams INT NOT NULL,        -- Popularité (en millions pour simplifier)
    UNIQUE(artist, title)
);

-- Insertion de 15 musiques variées pour le test
-- INSERT INTO songs (artist, title, snippet, year, country, genre, streams) VALUES
-- ('Queen', 'Bohemian Rhapsody', 'Is this the real life? Is this just fantasy?', 1975, 'UK', 'Rock', 2000),
-- ('Eminem', 'Lose Yourself', 'His palms are sweaty, knees weak, arms are heavy', 2002, 'USA', 'Rap', 1800),
-- ('Michael Jackson', 'Billie Jean', 'She was more like a beauty queen from a movie scene', 1982, 'USA', 'Pop', 1400),
-- ('Orelsan', 'La terre est ronde', 'Au fond j''crois qu''la terre est ronde, pour une seule bonne raison', 2011, 'France', 'Rap', 100),
-- ('Indochine', 'L''aventurier', 'Egaré dans la vallée infernale, le héros s''appelle Bob Morane', 1982, 'France', 'Rock', 50),
-- ('Stromae', 'Papaoutai', 'Dites-moi d''où il vient, enfin je saurai où je vais', 2013, 'Belgique', 'Pop', 900),
-- ('Daft Punk', 'Get Lucky', 'We''ve come too far to give up who we are', 2013, 'France', 'Electro', 1000),
-- ('Adele', 'Hello', 'Hello, it''s me', 2015, 'UK', 'Pop', 3000),
-- ('Nirvana', 'Smells Like Teen Spirit', 'Load up on guns, bring your friends', 1991, 'USA', 'Grunge', 1600),
-- ('Ed Sheeran', 'Shape of You', 'The club isn''t the best place to find a lover', 2017, 'UK', 'Pop', 3500),
-- ('Céline Dion', 'Pour que tu m''aimes encore', 'J''ai compris tous les mots, j''ai bien compris, merci', 1995, 'Canada', 'Pop', 200),
-- ('Linkin Park', 'In The End', 'I tried so hard and got so far', 2000, 'USA', 'Nu Metal', 1500),
-- ('Drake', 'God''s Plan', 'She say, "Do you love me?" I tell her, "Only partly"', 2018, 'Canada', 'Rap', 2200),
-- ('The Beatles', 'Hey Jude', 'Hey Jude, don''t make it bad', 1968, 'UK', 'Rock', 800),
-- ('Angèle', 'Tout oublier', 'Le spleen n''est plus à la mode, c''est pas compliqué d''être heureux', 2018, 'Belgique', 'Pop', 150);