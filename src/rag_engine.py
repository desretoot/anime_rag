import json
import os
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from config import DB_FOLDER, EMBEDDING_MODEL, LLM_TYPE
from src.utils import load_all_anime
from src.openrouter_client import openrouter_client, initialize_openrouter

class AnimeRAGEngine:
    def __init__(self, model_name=EMBEDDING_MODEL, use_llm=True):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.anime_data = []
        self.anime_ids = []
        self.use_llm = use_llm

    def prepare_data_for_embedding(self, anime_list):
        """Подготавливает текст для векторизации"""
        texts = []
        for anime in anime_list:
            # Комбинируем название, жанры и описание
            text_parts = []
            
            if anime.get('russian'):
                text_parts.append(anime['russian'])
            if anime.get('name'):
                text_parts.append(anime['name'])
            if anime.get('genres'):
                text_parts.append(' '.join(anime['genres']))
            if anime.get('description'):
                # Очищаем описание от HTML тегов если нужно
                desc = anime['description'].replace('<br>', ' ').replace('</br>', ' ')
                text_parts.append(desc)
                
            texts.append(' '.join(text_parts))
        
        return texts
    
    def build_index(self):
        """Создает векторный индекс"""
        print("Загружаем данные...")
        anime_list = load_all_anime()
        
        if not anime_list:
            print("Нет данных для построения индекса!")
            return
            
        print(f"Загружено {len(anime_list)} аниме")
        
        # Сохраняем данные для последующего использования
        self.anime_data = anime_list
        self.anime_ids = [str(anime['id']) for anime in anime_list]
        
        # Подготавливаем тексты для векторизации
        texts = self.prepare_data_for_embedding(anime_list)
        print(f"Подготовлено {len(texts)} текстов для векторизации")
        
        # Создаем векторные представления
        print("Создаем векторные представления...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Создаем FAISS индекс
        print("Создаем FAISS индекс...")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"Индекс создан! Размерность: {dimension}, Количество векторов: {self.index.ntotal}")
        
    def search(self, query, k=5):
        """Поиск похожих аниме по запросу"""
        if self.index is None:
            print("Индекс не создан! Сначала вызовите build_index()")
            return []
            
        # Векторизуем запрос
        query_embedding = self.model.encode([query])
        
        # Поиск ближайших соседей
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Формируем результаты
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.anime_data):
                anime = self.anime_data[idx]
                results.append({
                    'anime': anime,
                    'similarity': float(1 / (1 + distances[0][i]))  # Преобразуем расстояние в схожесть
                })
        
        return results
    
    def search_by_genres(self, genres_list, k=5):
        """Поиск по жанрам"""
        query = " ".join(genres_list)
        return self.search(query, k)
    
    def filter_by_rating(self, results, min_rating=0):
        """Фильтрация результатов по рейтингу"""
        filtered = []
        for result in results:
            score = result['anime'].get('score')
            if score and float(score) >= min_rating:
                filtered.append(result)
        return filtered
    
    def generate_response_with_llm(self, query, results):
        """Генерирует ответ с помощью LLM"""
        # Формируем контекст для LLM
        context = "Вот список аниме, которые подходят под запрос пользователя:\n\n"
        for i, result in enumerate(results, 1):
            anime = result['anime']
            name = anime.get('russian') or anime.get('name') or 'Без названия'
            genres = ', '.join(anime.get('genres', []))
            score = anime.get('score', 'N/A')
            episodes = anime.get('episodes', 'N/A')
            status = anime.get('status', 'N/A')
            
            context += f"{i}. {name}\n"
            context += f"   Жанры: {genres}\n"
            context += f"   Рейтинг: {score}, Эпизоды: {episodes}, Статус: {status}\n"
            if anime.get('description'):
                context += f"   Описание: {anime['description'][:300]}...\n\n"
            else:
                context += "\n"
        
        prompt = f"""Ты эксперт по аниме. Пользователь спросил: "{query}"

{context}

Сделай краткую, дружелюбную подборку этих аниме на русском языке. Объясни, почему они подходят под запрос. 
Ответ должен быть структурированным и понятным. Не используй markdown. Не упоминай названия, которых нет в списке.
Если в списке есть продолжения одного аниме, укажи это и порекомендуй смотреть по порядку.
"""

        try:
            if LLM_TYPE == "openrouter" and openrouter_client:
                response = openrouter_client.generate_response(prompt, max_tokens=1500, temperature=0.7)
                return response
            elif LLM_TYPE == "deepseek" and deepseek_client:
                response = deepseek_client.generate_response(prompt, max_tokens=1500, temperature=0.7)
                return response
            else:
                return self._format_fallback_response(results)
        except Exception as e:
            print(f"Ошибка при генерации ответа LLM: {e}")
            return self._format_fallback_response(results)
    
    def _format_fallback_response(self, results):
        """Форматирует ответ без LLM"""
        response = "🔍 Вот что я нашел для тебя:\n\n"
        for i, result in enumerate(results[:3], 1):
            anime = result['anime']
            name = anime.get('russian') or anime.get('name') or 'Без названия'
            score = anime.get('score', 'N/A')
            genres = ', '.join(anime.get('genres', []))
            url = anime.get('url', '#')
            response += f"🎬 {name} (⭐ {score})\n"
            response += f"🎭 Жанры: {genres}\n"
            response += f"🔗 {url}\n\n"
        return response

# Глобальный экземпляр движка
rag_engine = AnimeRAGEngine()

# В функции initialize_rag():
def initialize_rag():
    """Инициализация RAG-движка"""
    global rag_engine
    if rag_engine.index is None:
        rag_engine.build_index()
    
    # Инициализируем LLM если используется
    if LLM_TYPE == "openrouter":
        initialize_openrouter()
    elif LLM_TYPE == "deepseek":
        initialize_deepseek()
        
    return rag_engine