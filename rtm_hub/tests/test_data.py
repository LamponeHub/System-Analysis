# test_data.py - для наполнения базы тестовыми данными
test_requirements = [
    {"title": "Авторизация пользователя", "description": "Система должна поддерживать вход по логину/паролю", "priority": "High", "source": "BRD-001"},
    {"title": "Восстановление пароля", "description": "Пользователь может восстановить пароль через email", "priority": "Medium", "source": "BRD-001"},
    {"title": "Экспорт отчетов", "description": "Администратор может экспортировать данные в Excel", "priority": "Low", "source": "Интервью с заказчиком"},
    {"title": "Уведомления", "description": "Система отправляет email уведомления о событиях", "priority": "Medium", "source": "JIRA-456"},
    {"title": "Аудит действий", "description": "Все действия пользователей логируются", "priority": "High", "source": "NFR-003"},
]