# Как проверить, какой провайдер используется

## Признаки Mock провайдера:
- В "Parsed Output JSON" → "notes": "Mock extraction"
- В "Output Text" → "notes": "Mock extraction"
- Персоны не извлекаются (persons: [])
- Ответы очень простые и шаблонные
- Быстрая обработка (< 1 секунда)

## Признаки OpenAI провайдера:
- В "notes" нет "Mock extraction" (или notes отсутствует)
- Персоны извлекаются правильно
- Ответы более детальные и контекстуальные
- Обработка занимает 2-10 секунд
- В "Tokens" видны реальные значения (не 100/50)

## Как проверить текущий провайдер:

### Через переменные окружения:
```bash
docker-compose exec backend env | grep LLM_PROVIDER
```

Должно быть: `LLM_PROVIDER=openai`

### Через .env файл:
```bash
cat .env | grep LLM_PROVIDER
```

Должно быть: `LLM_PROVIDER=openai`

## Если используется Mock, но нужен OpenAI:

1. Проверьте .env файл:
   ```bash
   cat .env | grep LLM_PROVIDER
   ```

2. Если там `LLM_PROVIDER=mock`, измените на `openai`

3. Пересоздайте контейнер:
   ```bash
   docker-compose down backend
   docker-compose up -d backend
   ```

4. Проверьте:
   ```bash
   docker-compose exec backend env | grep LLM_PROVIDER
   ```

## Пример правильного ответа от OpenAI:

```json
{
  "memories": [
    {
      "summary": "Женитьба на Яне",
      "narrative": "Пять лет назад я женился на Яне. Она врач ортодонт...",
      "persons": [
        {
          "name": "Яна",
          "type": "romance",
          "confidence": 0.9
        },
        {
          "name": "Лиза",
          "type": "family",
          "confidence": 0.9
        }
      ]
    }
  ]
}
```

## Пример ответа от Mock (неправильно):

```json
{
  "memories": [
    {
      "summary": "Extracted memory from: ...",
      "persons": [],
      "notes": "Mock extraction"
    }
  ]
}
```
