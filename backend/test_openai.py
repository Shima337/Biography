#!/usr/bin/env python3
"""
Простой тест подключения к OpenAI API
Запуск: python test_openai.py
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import traceback

# Загружаем переменные окружения
load_dotenv()

def test_openai():
    """Тестирует подключение к OpenAI API"""
    
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К OPENAI API")
    print("=" * 60)
    print()
    
    # 1. Проверяем API ключ
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"1. Проверка API ключа...")
    if not api_key:
        print("   ❌ ОШИБКА: OPENAI_API_KEY не найден в переменных окружения!")
        print("   Проверьте файл .env в корне проекта")
        return False
    
    if api_key.startswith("your_") or api_key.startswith("sk-") == False:
        print(f"   ⚠️  ВНИМАНИЕ: API ключ выглядит неправильно: {api_key[:10]}...")
    else:
        print(f"   ✓ API ключ найден: {api_key[:20]}...")
    print()
    
    # 2. Создаём клиент
    print("2. Создание OpenAI клиента...")
    try:
        client = OpenAI(api_key=api_key)
        print("   ✓ Клиент создан успешно")
    except Exception as e:
        print(f"   ❌ ОШИБКА при создании клиента: {e}")
        traceback.print_exc()
        return False
    print()
    
    # 3. Простой тест запроса
    print("3. Тестовый запрос к API...")
    print("   Отправка: 'Привет, ответь одним словом: работает?'")
    print("   Ожидание ответа...")
    print()
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "user", "content": "Привет, ответь одним словом: работает?"}
            ],
            max_tokens=10,
            timeout=30.0  # 30 секунд таймаут (увеличено для диагностики)
        )
        
        answer = response.choices[0].message.content
        print(f"   ✓ УСПЕХ! Ответ получен: '{answer}'")
        print(f"   Токены использованы: {response.usage.total_tokens}")
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ ОШИБКА при запросе к API!")
        print()
        print("   ДЕТАЛИ ОШИБКИ:")
        print("   " + "=" * 56)
        print(f"   Тип ошибки: {type(e).__name__}")
        print(f"   Сообщение: {str(e)}")
        print()
        print("   ПОЛНЫЙ ТРЕЙС:")
        print("   " + "-" * 56)
        traceback.print_exc()
        print("   " + "=" * 56)
        print()
        
        # Дополнительная диагностика
        print("   ДИАГНОСТИКА:")
        print("   " + "-" * 56)
        
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            print("   → Проблема: Таймаут соединения")
            print("   → Возможные причины:")
            print("     • OpenAI API заблокирован в вашем регионе")
            print("     • Нет доступа к интернету")
            print("     • Блокировка файрволом/провайдером")
            print("     • Проблемы с DNS")
            print()
            print("   → РЕШЕНИЯ:")
            print("     1. Используйте VPN для доступа к OpenAI API")
            print("     2. Настройте прокси в коде (см. документацию OpenAI)")
            print("     3. Используйте альтернативные API (Anthropic, локальные модели)")
            print("     4. Временно используйте LLM_PROVIDER=mock для разработки")
        
        elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            print("   → Проблема: Ошибка аутентификации")
            print("   → Возможные причины:")
            print("     • Неправильный API ключ")
            print("     • API ключ истёк или заблокирован")
            print("     • Недостаточно средств на счёте OpenAI")
        
        elif "rate limit" in str(e).lower():
            print("   → Проблема: Превышен лимит запросов")
            print("   → Решение: Подождите немного и попробуйте снова")
        
        elif "api key" in str(e).lower():
            print("   → Проблема: Проблема с API ключом")
            print("   → Проверьте правильность ключа в .env файле")
        
        else:
            print("   → Неизвестная ошибка")
            print("   → Проверьте логи выше для деталей")
        
        print("   " + "=" * 56)
        print()
        return False

def test_network():
    """Проверяет доступность OpenAI API через простой HTTP запрос"""
    print("4. Проверка доступности OpenAI API...")
    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request("https://api.openai.com", method="HEAD")
        urllib.request.urlopen(req, timeout=10)
        print("   ✓ API доступен (базовый HTTP запрос прошёл)")
        return True
    except urllib.error.URLError as e:
        print(f"   ❌ Ошибка соединения: {e}")
        print("   → Проверьте интернет соединение")
        return False
    except Exception as e:
        print(f"   ⚠️  Не удалось проверить: {e}")
        return False

if __name__ == "__main__":
    print()
    
    # Проверка сети
    network_ok = test_network()
    print()
    
    # Основной тест
    success = test_openai()
    
    print()
    print("=" * 60)
    if success:
        print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("   OpenAI API работает корректно")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        print("   Смотрите ошибки выше для диагностики")
    print("=" * 60)
    print()
    
    sys.exit(0 if success else 1)
