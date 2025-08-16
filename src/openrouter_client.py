import requests
import json
from config import OPENROUTER_API_KEY

class OpenRouterClient:
    def __init__(self):
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "твой_ключ_после_регистрации":
            raise ValueError("OPENROUTER_API_KEY не задан в .env файле")
            
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        
    def generate_response(self, prompt, max_tokens=1000, temperature=0.7):
        """Генерирует ответ с помощью OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "mistralai/mistral-7b-instruct:free",  # Бесплатная модель
                "messages": [
                    {"role": "system", "content": "Ты эксперт по аниме. Отвечай на русском языке."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"Ошибка при генерации ответа OpenRouter: {e}")
            return None

# Глобальный экземпляр клиента
openrouter_client = None

def initialize_openrouter():
    """Инициализация OpenRouter клиента"""
    global openrouter_client
    try:
        openrouter_client = OpenRouterClient()
        return True
    except Exception as e:
        print(f"Не удалось инициализировать OpenRouter: {e}")
        return False

def test_openrouter():
    """Тестирование подключения к OpenRouter"""
    if initialize_openrouter():
        try:
            response = openrouter_client.generate_response("Привет! Ты работаешь?")
            if response:
                print("✅ OpenRouter API работает корректно!")
                print(f"Ответ: {response}")
                return True
            else:
                print("❌ OpenRouter API не отвечает")
                return False
        except Exception as e:
            print(f"❌ Ошибка при тестировании OpenRouter: {e}")
            return False
    return False