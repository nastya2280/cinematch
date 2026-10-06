ALTER TABLE movies
    ADD COLUMN IF NOT EXISTS runtime INT,
    ADD COLUMN IF NOT EXISTS tagline TEXT,
    ADD COLUMN IF NOT EXISTS details_loaded_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS people (
    id INT PRIMARY KEY,
    name TEXT NOT NULL,
    profile_path TEXT
);

CREATE TABLE IF NOT EXISTS movie_cast (
    movie_id INT REFERENCES movies(id) ON DELETE CASCADE,
    person_id INT REFERENCES people(id),
    character TEXT,
    cast_order INT,
    PRIMARY KEY (movie_id, person_id)
);

CREATE TABLE IF NOT EXISTS movie_directors (
    movie_id INT REFERENCES movies(id) ON DELETE CASCADE,
    person_id INT REFERENCES people(id),
    PRIMARY KEY (movie_id, person_id)
);

CREATE INDEX IF NOT EXISTS idx_cast_person
    ON movie_cast(person_id);