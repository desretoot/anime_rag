import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Пути
BASE_DIR = Path(__file__).parent
DB_FOLDER = BASE_DIR / "anime_database"
SRC_DIR = BASE_DIR / "src"

# Создаем папки если их нет
DB_FOLDER.mkdir(exist_ok=True)

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")

# GigaChat API
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

# User-Agent для Shikimori API
USER_AGENT = os.getenv("USER_AGENT", "AnimeRAGBot (your_email@example.com)")

# Shikimori API
SHIKIMORI_BASE_URL = "https://shikimori.one/api"

# Модель для векторизации
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Добавь в конец:
LLM_TYPE = os.getenv("LLM_TYPE", "deepseek")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Добавь в конец:
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")