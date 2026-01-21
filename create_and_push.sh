#!/bin/bash

# Скрипт для создания репозитория и пуша v1

cd ~/Biography

echo "🚀 Создание репозитория Biography на GitHub..."

# Вариант 1: Через GitHub CLI (если авторизован)
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI авторизован, создаю репозиторий..."
    gh repo create Biography \
        --public \
        --description "LifeBook Lab Console - AI Memory Extraction Debugging Tool" \
        --source=. \
        --remote=origin \
        --push
    
    if [ $? -eq 0 ]; then
        echo "✅ Репозиторий создан и код отправлен!"
        echo "🌐 https://github.com/Shima337/Biography"
        exit 0
    fi
fi

# Вариант 2: Если GitHub CLI не авторизован, пробуем push (если репозиторий уже создан)
echo "Пробую запушить в существующий репозиторий..."
git push -u origin main 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Код успешно отправлен!"
    echo "🌐 https://github.com/Shima337/Biography"
    exit 0
fi

# Вариант 3: Инструкции
echo ""
echo "⚠️  Репозиторий нужно создать вручную:"
echo ""
echo "1. Откройте: https://github.com/new"
echo "2. Repository name: Biography"
echo "3. Description: LifeBook Lab Console - AI Memory Extraction Debugging Tool"
echo "4. Выберите Public"
echo "5. НЕ ставьте галочки на README, .gitignore, license"
echo "6. Нажмите 'Create repository'"
echo ""
echo "После создания выполните:"
echo "  cd ~/Biography"
echo "  git push -u origin main"
echo ""
