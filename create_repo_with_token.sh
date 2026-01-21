#!/bin/bash

# Создание репозитория через GitHub API с токеном

cd ~/Biography

echo "🔐 Создание репозитория через GitHub API"
echo ""
echo "Для создания репозитория нужен Personal Access Token"
echo ""
echo "Если у вас есть токен, выполните:"
echo "  export GITHUB_TOKEN=your_token_here"
echo "  ./create_repo_with_token.sh"
echo ""
echo "Или создайте токен:"
echo "  1. Откройте: https://github.com/settings/tokens"
echo "  2. Generate new token (classic)"
echo "  3. Выберите scope: repo"
echo "  4. Скопируйте токен"
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN не установлен"
    echo ""
    read -p "Введите ваш GitHub Personal Access Token: " token
    export GITHUB_TOKEN=$token
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Токен не предоставлен"
    exit 1
fi

echo "🚀 Создание репозитория..."

response=$(curl -s -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{
    "name": "Biography",
    "description": "LifeBook Lab Console - AI Memory Extraction Debugging Tool",
    "private": false
  }')

if echo "$response" | grep -q '"name":"Biography"'; then
    echo "✅ Репозиторий создан!"
    echo ""
    echo "📤 Отправка кода..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Код успешно отправлен!"
        echo "🌐 https://github.com/Shima337/Biography"
    else
        echo "❌ Ошибка при отправке кода"
    fi
else
    echo "❌ Ошибка при создании репозитория:"
    echo "$response" | head -5
fi
