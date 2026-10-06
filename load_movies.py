import os
import time

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

BASE = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('TMDB_TOKEN')}",
    "accept": "application/json",
}
PAGES = 50  # 250 страниц * 20 фильмов = 5000


def tmdb_get(path, **params):
    """GET-запрос к TMDB с повтором, если нас притормозили (429)."""
    params.setdefault("language", "ru-RU")
    for _ in range(5):
        r = requests.get(BASE + path, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 2)))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"TMDB не ответил нормально: {path}")


def main():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    # 1. Жанры (сначала, потому что movie_genres ссылается на них)
    genres = tmdb_get("/genre/movie/list")["genres"]
    execute_values(
        cur,
        """INSERT INTO genres (id, name) VALUES %s
           ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""",
        [(g["id"], g["name"]) for g in genres],
    )
    conn.commit()
    print(f"Жанров загружено: {len(genres)}")

    # 2. Фильмы постранично
    for page in range(1, PAGES + 1):
        data = tmdb_get(
            "/discover/movie",
            sort_by="vote_count.desc",
            include_adult="false",
            page=page,
        )

        movie_rows, link_rows = [], []
        for m in data["results"]:
            movie_rows.append((
                m["id"],
                m["title"],
                m.get("original_title"),
                m.get("overview") or None,
                m.get("release_date") or None,   # пустая строка -> NULL
                m.get("original_language"),
                m.get("vote_average"),
                m.get("vote_count"),
                m.get("popularity"),
                m.get("poster_path"),
                m.get("backdrop_path"),
            ))
            for gid in m.get("genre_ids", []):
                link_rows.append((m["id"], gid))

        execute_values(
            cur,
            """INSERT INTO movies
               (id, title, original_title, overview, release_date, original_language,
                vote_average, vote_count, popularity, poster_path, backdrop_path)
               VALUES %s
               ON CONFLICT (id) DO UPDATE SET
                   vote_average = EXCLUDED.vote_average,
                   vote_count   = EXCLUDED.vote_count,
                   popularity   = EXCLUDED.popularity,
                   updated_at   = now()""",
            movie_rows,
        )
        if link_rows:
            execute_values(
                cur,
                "INSERT INTO movie_genres (movie_id, genre_id) VALUES %s ON CONFLICT DO NOTHING",
                link_rows,
            )
        conn.commit()  # сохраняем после каждой страницы

        print(f"Страница {page}/{PAGES} готова")
        time.sleep(0.25)  # не нагружаем API

    cur.close()
    conn.close()
    print("Готово!")


if __name__ == "__main__":
    main()