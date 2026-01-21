# GPT-5.2 - Информация о модели

## ✅ GPT-5.2 существует!

GPT-5.2 - это **флагманская модель OpenAI** для кодирования и агентских задач.

## 📊 Характеристики GPT-5.2

### Основные параметры:
- **Reasoning.effort**: none (default), low, medium, high, xhigh
- **Контекстное окно**: 400,000 токенов
- **Максимальный вывод**: 128,000 токенов
- **Knowledge cutoff**: 31 августа 2025
- **Поддержка Reasoning tokens**: Да

### Модальности:
- **Text**: Input и Output
- **Image**: Input only
- **Audio**: Not supported
- **Video**: Not supported

### Цены:
- **Input**: $1.75 за 1M токенов
- **Cached input**: $0.175 за 1M токенов
- **Output**: $14.00 за 1M токенов

### Сравнение с другими моделями:
- **GPT-5.2**: $1.75 / $14.00
- **GPT-5**: $1.25 / $14.00
- **GPT-5 mini**: $0.25 / $14.00

### Endpoints:
- ✅ Chat Completions (v1/chat/completions)
- ✅ Responses (v1/responses)
- ✅ Realtime (v1/realtime)
- ✅ Assistants (v1/assistants)
- ✅ Batch (v1/batch)
- ❌ Fine-tuning (v1/fine-tuning)
- ✅ Embeddings (v1/embeddings)

### Features:
- ✅ Streaming
- ✅ Function calling
- ✅ Structured outputs
- ✅ Distillation
- ❌ Fine-tuning

### Tools (через Responses API):
- ✅ Web search
- ✅ File search
- ✅ Image generation
- ✅ Code interpreter
- ✅ MCP
- ❌ Computer use

## 🚀 Использование в проекте

После пуша v1, обновим модель на `gpt-5.2`:

```python
# backend/app/service.py
self.model = os.getenv("OPENAI_MODEL", "gpt-5.2")
```

## 📝 Источник

Документация: https://platform.openai.com/docs/models/gpt-5.2
