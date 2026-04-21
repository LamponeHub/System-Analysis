"""
Генератор безопасного SECRET_KEY для JWT
"""

import secrets

def generate_secret_key(length: int = 32) -> str:
    """
    Генерирует криптографически стойкий случайный ключ
    """
    return secrets.token_hex(length)

if __name__ == "__main__":
    print("🔐 Генератор SECRET_KEY для StatementFlow\n")
    print("Скопируйте этот ключ в файл .env:\n")
    print(f"SECRET_KEY={generate_secret_key()}")
    print("\n" + "=" * 50)
    print("⚠️  Никому не показывайте этот ключ!")
    print("⚠️  Используйте уникальный ключ для каждого проекта!")