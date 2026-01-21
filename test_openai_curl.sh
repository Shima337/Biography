#!/bin/bash
# Скрипт для проверки доступа к OpenAI API через curl

echo "============================================================"
echo "ТЕСТ ДОСТУПА К OPENAI API ЧЕРЕЗ CURL"
echo "============================================================"
echo ""

# Читаем API ключ из .env
API_KEY=$(grep OPENAI_API_KEY ../.env | cut -d '=' -f2 | tr -d '"' | tr -d "'")

if [ -z "$API_KEY" ]; then
    echo "❌ ОШИБКА: OPENAI_API_KEY не найден в .env файле"
    exit 1
fi

echo "1. Проверка базового доступа к api.openai.com..."
echo "   Команда: curl -I https://api.openai.com --max-time 10"
echo ""
if curl -I https://api.openai.com --max-time 10 -s -o /dev/null -w "%{http_code}\n" | grep -q "200\|301\|302"; then
    echo "   ✓ API доступен (HTTP статус OK)"
else
    echo "   ❌ API недоступен (таймаут или ошибка)"
fi
echo ""

echo "2. Проверка списка моделей (без аутентификации)..."
echo "   Команда: curl https://api.openai.com/v1/models"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" https://api.openai.com/v1/models --max-time 10)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ API доступен! (401 = требуется аутентификация, это нормально)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ API доступен и работает!"
elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    echo "   ❌ Таймаут или нет соединения"
else
    echo "   ⚠️  HTTP код: $HTTP_CODE"
    echo "   Ответ: $BODY" | head -3
fi
echo ""

echo "3. Тестовый запрос к Chat Completions API..."
echo "   Команда: curl -X POST https://api.openai.com/v1/chat/completions"
echo ""
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST https://api.openai.com/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 5
    }' \
    --max-time 30)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "   HTTP код: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ УСПЕХ! API работает!"
    echo "   Ответ:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "   ❌ Ошибка аутентификации (401)"
    echo "   Проверьте правильность API ключа"
    echo "   Ответ: $BODY" | head -5
elif [ "$HTTP_CODE" = "429" ]; then
    echo "   ⚠️  Превышен лимит запросов (429)"
    echo "   Подождите немного и попробуйте снова"
elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    echo "   ❌ Таймаут соединения"
    echo "   OpenAI API недоступен из вашей сети"
    echo "   → Используйте VPN или прокси"
else
    echo "   ⚠️  Ошибка: HTTP $HTTP_CODE"
    echo "   Ответ: $BODY" | head -10
fi

echo ""
echo "============================================================"
echo "ГОТОВЫЕ КОМАНДЫ ДЛЯ РУЧНОГО ТЕСТИРОВАНИЯ:"
echo "============================================================"
echo ""
echo "# 1. Проверка доступности API:"
echo "curl -I https://api.openai.com --max-time 10"
echo ""
echo "# 2. Список моделей (покажет 401 без ключа, это нормально):"
echo "curl https://api.openai.com/v1/models --max-time 10"
echo ""
echo "# 3. Тестовый запрос (замените YOUR_API_KEY):"
echo 'curl -X POST https://api.openai.com/v1/chat/completions \'
echo '  -H "Content-Type: application/json" \'
echo "  -H \"Authorization: Bearer YOUR_API_KEY\" \\"
echo '  -d '"'"'{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'"'"' \'
echo '  --max-time 30'
echo ""
echo "# 4. С вашим ключом из .env:"
echo "curl -X POST https://api.openai.com/v1/chat/completions \\"
echo '  -H "Content-Type: application/json" \'
echo "  -H \"Authorization: Bearer $API_KEY\" \\"
echo '  -d '"'"'{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'"'"' \'
echo '  --max-time 30'
echo ""
