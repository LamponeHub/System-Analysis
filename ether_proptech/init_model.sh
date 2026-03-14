#!/bin/bash
set -e

echo "🌌 Инициализация нейросетевого ядра 'Эфир'..."

MODEL_NAME=${1:-"qwen2.5:7b-instruct"}

# Проверка наличия ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama не найден в системе. Пожалуйста, установите его или запустите через docker-compose."
    exit 1
fi

echo "⬇️ Загрузка модели $MODEL_NAME (это может занять время в зависимости от скорости интернета)..."
echo "💡 После загрузки система будет работать полностью оффлайн."

ollama pull $MODEL_NAME

if [ $? -eq 0 ]; then
    echo "✅ Модель успешно загружена и готова к работе."
    echo "✨ Теперь вы можете запустить проект командой: docker-compose up -d"
else
    echo "❌ Ошибка при загрузке модели. Проверьте соединение."
    exit 1
fi