#!/bin/bash
set -e

echo "🔍 Начало валидации документации..."

# 1. Проверка наличия всех файлов в папке docs/regulations
if [ ! -d "docs/regulations" ]; then
    echo "❌ Ошибка: Папка docs/regulations не найдена."
    exit 1
fi

# 2. Проверка синтаксиса Markdown (требуется установленный markdownlint)
# Если линтер ругается — сборка падает
if command -v markdownlint &> /dev/null; then
    echo "✅ Запуск markdownlint..."
    markdownlint docs/**/*.md || {
        echo "❌ Ошибки форматирования Markdown. Исправьте перед коммитом."
        exit 1
    }
else
    echo "⚠️ markdownlint не установлен, пропускаем проверку стиля."
fi

# 3. Проверка обязательных заголовков в каждом файле регламента
for file in docs/regulations/*.md; do
    if ! grep -q "^# " "$file"; then
        echo "❌ Ошибка в файле $file: Отсутствует главный заголовок (# Название)."
        exit 1
    fi
    if ! grep -q "ГОСТ\|СанПиН\|Регламент" "$file";
    then
        echo "⚠️ Предупреждение в файле $file: Возможно, отсутствует ссылка на нормативный акт в названии или начале."
    fi
done

echo "✅ Все документы прошли валидацию. Можно формировать образ."