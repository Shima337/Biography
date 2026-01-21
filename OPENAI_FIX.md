# Решение проблемы с доступом к OpenAI API

## Проблема
OpenAI API (`api.openai.com`) недоступен из вашей сети - таймаут соединения.

## Диагностика
Запустите тест:
```bash
cd backend
python3 test_openai.py
```

## Решения

### 1. Использовать VPN (рекомендуется)
- Включите VPN
- Запустите тест снова: `python3 test_openai.py`
- Если работает - настройте VPN для Docker контейнера

### 2. Настроить прокси в коде
Добавьте в `backend/app/llm_provider.py`:
```python
from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    http_client=httpx.Client(
        proxies="http://your-proxy:port"  # ваш прокси
    )
)
```

### 3. Использовать mock провайдер (для разработки)
В `.env`:
```env
LLM_PROVIDER=mock
```
Это работает мгновенно без API.

### 4. Альтернативные API
- Anthropic Claude API
- Локальные модели (Ollama, LM Studio)
- Другие провайдеры

## Текущий статус
✅ Тест-файл создан: `backend/test_openai.py`
✅ Mock провайдер работает
❌ OpenAI API недоступен (нужен VPN/прокси)
