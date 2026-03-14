import re

class ResponseValidator:
    def __init__(self):
        # Паттерн для поиска ссылок вида [Документ, п. X.X]
        self.citation_pattern = re.compile(r'\[.*?,\s*п\.?\s*\d+.*?\]')

    def validate(self, response_text: str, source_context: list[str]) -> bool:
        """
        Проверяет, содержит ли ответ цитату из источника.
        Если ответ не содержит ссылок на регламент — он отклоняется.
        """
        if not self.citation_pattern.search(response_text):
            return False
        
        # Дополнительная проверка: убедиться, что cited документ реально есть в контексте
        # (упрощенная логика для примера)
        return True

    def sanitize(self, response: str) -> str:
        if not self.validate(response, []):
            return "Ошибка генерации: Ответ не прошел проверку на соответствие нормативной базе. Требуется ручное вмешательство."
        return response