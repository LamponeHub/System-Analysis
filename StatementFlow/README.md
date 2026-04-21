# StatementFlow

Система для создания и управления заявлениями в правоохранительные органы.

## Возможности

- ✅ Веб-интерфейс с аутентификацией
- ✅ Telegram-бот для создания заявлений
- ✅ Генерация PDF-документов
- ✅ Отслеживание статусов заявлений
- ✅ Приватные данные пользователей

## Быстрый старт

```bash
# Клонирование
git clone <repository-url>
cd statement_flow

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка
cp .env.example .env
# Отредактируйте .env и добавьте TELEGRAM_BOT_TOKEN

# Запуск веб-приложения
uvicorn main:app --reload

# Запуск бота (в отдельном терминале)
python bot.py