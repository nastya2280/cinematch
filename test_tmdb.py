import os

import requests
from dotenv import load_dotenv


# Загружаем переменные из файла .env
load_dotenv()

# Получаем наш секретный TMDB-токен
TOKEN = os.getenv("TMDB_TOKEN")

# 603 — ID фильма The Matrix в TMDB
url = "https://api.themoviedb.org/3/movie/603"

# Передаём токен TMDB
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "accept": "application/json"
}

# Просим TMDB вернуть русскую локализацию
params = {
    "language": "ru-RU"
}

# Отправляем GET-запрос
response = requests.get(
    url,
    headers=headers,
    params=params
)

# Смотрим HTTP-код ответа
print("Статус:", response.status_code)

# Смотрим данные
print(response.json())