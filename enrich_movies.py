import os
import time

import psycopg2
from dotenv import load_dotenv

from load_movies import tmdb_get

load_dotenv()

LIMIT = 1000       # сначала проверяем на одном фильме
TOP_CAST = 10

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

cur = conn.cursor()

cur.execute("""
    SELECT id
    FROM movies
    WHERE details_loaded_at IS NULL
    ORDER BY vote_count DESC
    LIMIT %s
""", (LIMIT,))

ids = [row[0] for row in cur.fetchall()]

for i, movie_id in enumerate(ids, 1):
    print(f"Загружается фильм {movie_id}...")

    details = tmdb_get(
        f"/movie/{movie_id}",
        append_to_response="credits"
    )

    cur.execute("""
        UPDATE movies
        SET runtime = %s,
            tagline = %s,
            details_loaded_at = now()
        WHERE id = %s
    """, (
        details.get("runtime"),
        details.get("tagline") or None,
        movie_id
    ))

    credits = details.get("credits", {})

    for actor in credits.get("cast", [])[:TOP_CAST]:
        cur.execute("""
            INSERT INTO people (id, name, profile_path)
            VALUES (%s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                profile_path = EXCLUDED.profile_path
        """, (
            actor["id"],
            actor["name"],
            actor.get("profile_path")
        ))

        cur.execute("""
            INSERT INTO movie_cast
                (movie_id, person_id, character, cast_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            movie_id,
            actor["id"],
            actor.get("character"),
            actor.get("order")
        ))

    for employee in credits.get("crew", []):
        if employee.get("job") == "Director":
            cur.execute("""
                INSERT INTO people (id, name, profile_path)
                VALUES (%s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    profile_path = EXCLUDED.profile_path
            """, (
                employee["id"],
                employee["name"],
                employee.get("profile_path")
            ))

            cur.execute("""
                INSERT INTO movie_directors (movie_id, person_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (
                movie_id,
                employee["id"]
            ))

    conn.commit()
    print(f"{i}/{len(ids)}: фильм {movie_id} обработан")

    time.sleep(0.25)

cur.close()
conn.close()

print("Подробности загружены!")