import json
import os
from config import DB_FOLDER

def load_all_anime():
    """Загружает все аниме из базы данных"""
    anime_list = []
    
    for filename in os.listdir(DB_FOLDER):
        if filename.endswith('.json') and filename != 'index.json':
            filepath = os.path.join(DB_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    anime_data = json.load(f)
                    anime_list.append(anime_data)
            except Exception as e:
                print(f"Ошибка при загрузке {filename}: {e}")
    
    return anime_list

def get_anime_by_id(anime_id):
    """Получает аниме по ID"""
    filepath = os.path.join(DB_FOLDER, f"{anime_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None