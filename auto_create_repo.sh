#!/bin/bash

# Автоматическое создание репозитория через GitHub CLI

cd ~/Biography
eval "$(/opt/homebrew/bin/brew shellenv)"

echo "🔐 Проверка авторизации GitHub CLI..."

# Проверяем авторизацию
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI уже авторизован"
else
    echo "⚠️  Требуется авторизация в GitHub CLI"
    echo ""
    echo "Выполните вручную:"
    echo "  gh auth login"
    echo ""
    echo "Выберите:"
    echo "  1. GitHub.com"
    echo "  2. SSH"
    echo "  3. Авторизуйтесь через браузер"
    echo ""
    exit 1
fi

echo ""
echo "🚀 Создание репозитория Biography на GitHub..."

gh repo create Biography \
    --public \
    --description "LifeBook Lab Console - AI Memory Extraction Debugging Tool" \
    --source=. \
    --remote=origin \
    --push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Репозиторий создан и код отправлен!"
    echo "🌐 https://github.com/Shima337/Biography"
else
    echo ""
    echo "❌ Ошибка при создании репозитория"
    exit 1
fi
