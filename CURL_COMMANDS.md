# Curl команды для тестирования OpenAI API

## Быстрая проверка доступности

```bash
# 1. Проверка базового доступа
curl -I https://api.openai.com --max-time 10
```

Если видите HTTP заголовки (200, 301, 302) - API доступен.
Если таймаут - API заблокирован.

---

## Проверка без аутентификации

```bash
# 2. Список моделей (вернёт 401 - это нормально, значит API доступен)
curl https://api.openai.com/v1/models --max-time 10
```

Ожидаемый ответ: `{"error":{"message":"Incorrect API key provided...","type":"invalid_request_error"...}}`
Это значит, что API доступен, просто нужен ключ.

---

## Полный тест с API ключом

```bash
# 3. Тестовый запрос (замените YOUR_API_KEY на ваш ключ)
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 5
  }' \
  --max-time 30
```

**С вашим ключом из .env:**
```bash
# Читаем ключ из .env
API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")

# Используем в запросе
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 5
  }' \
  --max-time 30
```

---

## Автоматический скрипт

Запустите готовый скрипт:
```bash
cd Biography
./test_openai_curl.sh
```

Или:
```bash
bash test_openai_curl.sh
```

---

## Интерпретация результатов

### ✅ Успех (HTTP 200)
```json
{
  "id": "chatcmpl-...",
  "choices": [{"message": {"content": "Hello"}}]
}
```
**→ API работает! Можно использовать в приложении.**

### ❌ Таймаут (HTTP 000 или нет ответа)
```
curl: (28) Operation timed out
```
**→ API недоступен. Нужен VPN/прокси.**

### ⚠️ 401 Unauthorized
```json
{"error": {"message": "Incorrect API key provided"}}
```
**→ API доступен, но ключ неправильный. Проверьте .env**

### ⚠️ 429 Rate Limit
```json
{"error": {"message": "Rate limit exceeded"}}
```
**→ Превышен лимит. Подождите и попробуйте снова.**

---

## Быстрая команда одной строкой

```bash
curl -X POST https://api.openai.com/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $(grep OPENAI_API_KEY .env | cut -d '=' -f2)" -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}' --max-time 30
```
