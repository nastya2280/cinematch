CREATE TABLE IF NOT EXISTS genres (
    id INT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movies (
    id INT PRIMARY KEY,
    title TEXT NOT NULL,
    original_title TEXT,
    overview TEXT,
    release_date DATE,
    original_language TEXT,
    vote_average NUMERIC(5,3),
    vote_count INT,
    popularity NUMERIC,
    poster_path TEXT,
    backdrop_path TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INT REFERENCES movies(id) ON DELETE CASCADE,
    genre_id INT REFERENCES genres(id),
    PRIMARY KEY (movie_id, genre_id)
);

CREATE INDEX IF NOT EXISTS idx_movie_genres_genre
    ON movie_genres(genre_id);

CREATE INDEX IF NOT EXISTS idx_movies_rating
    ON movies(vote_average);