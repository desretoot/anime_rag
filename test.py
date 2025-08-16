import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.openrouter_client import test_openrouter

if __name__ == "__main__":
    print("🔍 Тестируем подключение к DeepSeek API...")
    success = test_openrouter()
    if success:
        print("✅ DeepSeek API работает корректно!")
    else:
        print("❌ Не удалось подключиться к DeepSeek API")
        print("Проверьте ваш DEEPSEEK_API_KEY в .env файле")