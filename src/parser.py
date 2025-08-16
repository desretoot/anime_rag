import requests
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import json
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from config import SHIKIMORI_BASE_URL, USER_AGENT, DB_FOLDER

HEADERS = {
    "User-Agent": USER_AGENT
}

def fetch_anime(page=1, limit=50, kind="tv"):
    params = {
        "page": page,
        "limit": limit,
        "kind": kind,
        "order": "popularity",
        "status": None
    }
    response = requests.get(f"{SHIKIMORI_BASE_URL}/animes", headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка на странице {page}: {response.status_code}")
        return []

def fetch_anime_details(anime_id):
    response = requests.get(f"{SHIKIMORI_BASE_URL}/animes/{anime_id}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print(f"429 Too Many Requests для аниме {anime_id}, ждем...")
        time.sleep(5)
        return fetch_anime_details(anime_id)
    else:
        print(f"Ошибка при получении аниме {anime_id}: {response.status_code}")
        return {}

def load_existing_database():
    """Загружает существующую базу данных"""
    all_anime = {}
    
    for filename in os.listdir(DB_FOLDER):
        if filename.endswith('.json') and filename != 'index.json':
            filepath = os.path.join(DB_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    anime_data = json.load(f)
                    all_anime[anime_data['id']] = anime_data
            except Exception as e:
                print(f"Ошибка при загрузке {filename}: {e}")
    
    return all_anime

def save_anime_data(anime_data):
    """Сохраняет данные об одном аниме в отдельный файл"""
    filename = f"{anime_data['id']}.json"
    filepath = os.path.join(DB_FOLDER, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(anime_data, f, ensure_ascii=False, indent=4)

def main():
    # Загружаем существующую базу
    existing_anime = load_existing_database()
    print(f"Загружено {len(existing_anime)} существующих записей")

    # Сбор новых данных
    new_anime_count = 0
    total_pages = 20

    for page in tqdm(range(1, total_pages + 1), desc="Парсинг страниц"):
        batch = fetch_anime(page=page, limit=50)
        if not batch:
            break

        for item in batch:
            anime_id = item["id"]
            
            # Если аниме уже есть в базе, пропускаем
            if anime_id in existing_anime:
                continue
                
            # Получаем полную информацию
            full_data = fetch_anime_details(anime_id)
            if full_data:
                anime_record = {
                    "id": full_data.get("id"),
                    "name": full_data.get("name"),
                    "russian": full_data.get("russian"),
                    "description": full_data.get("description"),
                    "score": full_data.get("score"),
                    "episodes": full_data.get("episodes"),
                    "episodes_aired": full_data.get("episodes_aired"),
                    "status": full_data.get("status"),
                    "genres": [g["russian"] for g in full_data.get("genres", [])],
                    "url": f"https://shikimori.one/animes/{full_data.get('id')}-{full_data.get('name', '').replace(' ', '-')}",
                    "aired_on": full_data.get("aired_on"),
                    "studios": [s["name"] for s in full_data.get("studios", [])],
                    "parsed_at": datetime.now().isoformat()
                }
                
                save_anime_data(anime_record)
                existing_anime[anime_id] = anime_record
                new_anime_count += 1
                
            time.sleep(0.7)

        time.sleep(1)

    print(f"Добавлено новых аниме: {new_anime_count}")
    print(f"Всего аниме в базе: {len(existing_anime)}")

    # Создаем индекс
    index_data = {
        "updated_at": datetime.now().isoformat(),
        "total_count": len(existing_anime),
        "anime_ids": list(existing_anime.keys())
    }

    with open(os.path.join(DB_FOLDER, "index.json"), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=4)

    print("База данных обновлена успешно!")

if __name__ == "__main__":
    main()