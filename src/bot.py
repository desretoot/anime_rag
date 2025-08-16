import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, LLM_TYPE
from src.rag_engine import initialize_rag, rag_engine

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация RAG
rag_engine_instance = initialize_rag()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = f"""
🤖 Привет! Я Anime Recommender Bot с {LLM_TYPE.upper()}!

Я могу порекомендовать тебе аниме на основе твоих предпочтений, используя интеллектуальный поиск и {LLM_TYPE.upper()} для красивых ответов.

Просто напиши что-то вроде:
• "Посоветуй аниме в жанре ужасы"
• "Что посмотреть в жанре фэнтези и приключения?"
• "Аниме про школу и романтику"

И я подберу для тебя лучшие варианты! 🍿
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
Доступные команды:
/start - Начало работы
/help - Помощь
/about - О боте

Просто отправь мне сообщение с описанием того, что ты хочешь посмотреть, и я порекомендую подходящие аниме!

Примеры запросов:
• "Аниме в жанре хоррор и мистика"
• "Посоветуй что-нибудь интересное про космос"
• "Аниме про спорт для подростков"
    """
    await update.message.reply_text(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /about"""
    about_text = f"""
🤖 Anime Recommender Bot ({LLM_TYPE.upper()} Edition)

Этот бот использует технологию Retrieval-Augmented Generation (RAG) с интеграцией {LLM_TYPE.upper()} для поиска и рекомендации аниме.

База данных собрана с shikimori.one
Используются технологии: 
• Python, Telegram Bot API
• Sentence Transformers, FAISS (для поиска)
• {LLM_TYPE.upper()} API (для генерации ответов)

Создано как pet-проект для демонстрации RAG-систем с русскоязычной LLM.
    """
    await update.message.reply_text(about_text)

def format_anime_response(anime_data, similarity=None):
    """Форматирует ответ с информацией об аниме"""
    name = anime_data.get('russian') or anime_data.get('name') or 'Без названия'
    score = anime_data.get('score', 'N/A')
    episodes = anime_data.get('episodes', 'N/A')
    status = anime_data.get('status', 'N/A')
    genres = ', '.join(anime_data.get('genres', [])) if anime_data.get('genres') else 'N/A'
    url = anime_data.get('url', '#')
    
    description = anime_data.get('description', '')[:200] + '...' if anime_data.get('description') else 'Описание отсутствует'
    
    response = f"🎬 <b>{name}</b>\n"
    response += f"⭐ Рейтинг: {score}\n"
    response += f"📺 Эпизоды: {episodes}\n"
    response += f"📊 Статус: {status}\n"
    response += f"🎭 Жанры: {genres}\n\n"
    response += f"📝 {description}\n\n"
    response += f"🔗 <a href='{url}'>Подробнее на Shikimori</a>"
    
    if similarity:
        response += f"\n🎯 Релевантность: {similarity:.2f}"
    
    return response

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    logger.info(f"Получено сообщение: {user_message}")
    
    try:
        # Поиск похожих аниме
        results = rag_engine_instance.search(user_message, k=5)  # Увеличиваем до 5 для лучшего контекста
        
        if not results:
            await update.message.reply_text(
                "К сожалению, я не нашел подходящих аниме. Попробуй изменить запрос!",
                parse_mode='HTML'
            )
            return
        
        # Фильтруем по рейтингу если нужно
        results = rag_engine_instance.filter_by_rating(results, min_rating=5.0)
        
        if not results:
            await update.message.reply_text(
                "Не нашел аниме с хорошим рейтингом по вашему запросу. Попробуйте изменить запрос!",
                parse_mode='HTML'
            )
            return
        
        # Если включена LLM - генерируем красивый ответ
        if rag_engine_instance.use_llm and LLM_TYPE == "deepseek":
            llm_response = rag_engine_instance.generate_response_with_llm(user_message, results[:3])  # Берем топ-3
            if llm_response:
                await update.message.reply_text(llm_response)
                return
        
        # Если LLM не сработал - обычный ответ
        response = "🔍 Вот что я нашел для тебя:\n\n"
        for i, result in enumerate(results[:3], 1):  # Показываем только топ-3
            anime = result['anime']
            similarity = result['similarity']
            response += f"{format_anime_response(anime, similarity)}\n"
            response += "─" * 30 + "\n"
        
        await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(
            "Произошла ошибка при поиске. Попробуйте позже!",
            parse_mode='HTML'
        )

def main():
    """Основная функция запуска бота"""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Пожалуйста, установите TELEGRAM_TOKEN в config.py или .env файле")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    print("Бот запущен! Нажмите Ctrl+C для остановки")
    application.run_polling()

if __name__ == '__main__':
    main()