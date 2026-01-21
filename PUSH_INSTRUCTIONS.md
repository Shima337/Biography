# Инструкция по пушу v1 на GitHub

## ✅ Коммит уже сделан!

Версия v1 закоммичена локально. Теперь нужно создать репозиторий на GitHub и запушить.

## 🚀 Быстрый способ (через веб):

1. Откройте: https://github.com/new
2. **Repository name**: `Biography`
3. **Description**: "LifeBook Lab Console - AI Memory Extraction Debugging Tool"
4. Выберите **Public**
5. **НЕ** ставьте галочки на:
   - ❌ Add a README file
   - ❌ Add .gitignore  
   - ❌ Choose a license
   (Всё уже есть локально!)
6. Нажмите **"Create repository"**

7. После создания выполните в терминале:
```bash
cd ~/Biography
git push -u origin main
```

## 🔐 Альтернатива (через GitHub CLI):

Если хотите авторизоваться в GitHub CLI:

```bash
gh auth login
# Выберите SSH, затем браузер для авторизации

# После авторизации:
cd ~/Biography
gh repo create Biography --public --description "LifeBook Lab Console" --source=. --remote=origin --push
```

## ✅ После пуша:

Репозиторий будет доступен по адресу:
https://github.com/Shima337/Biography
