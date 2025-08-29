# ==============================================
# КОНФИГУРАЦИЯ БОТА - ОСНОВНЫЕ НАСТРОЙКИ
# ==============================================
# Этот файл содержит все основные настройки проекта
# Изменяйте только значения, структуру не трогайте

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def check_required_env_vars():
    """Проверяет наличие всех необходимых переменных окружения"""
    required_vars = {
        "BOT_TOKEN": "Токен Telegram бота",
        "WORK_CHAT_ID": "ID рабочего чата",
        "JIRA_LOGIN": "Логин Jira",
        "JIRA_PASSWORD": "Пароль Jira"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ ОШИБКА: Отсутствуют обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📋 Создайте файл .env на основе pass.env и переименуйте его в .env")
        print("🔍 Подробности в ENV_SETUP.md")
        sys.exit(1)

# Проверяем переменные окружения при импорте
check_required_env_vars()

# ============== TELEGRAM НАСТРОЙКИ ==============
# Токен бота (получен от @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID рабочего чата для уведомлений
WORK_CHAT_ID = int(os.getenv("WORK_CHAT_ID"))

# ============== JIRA НАСТРОЙКИ ==============
# Логин и пароль для Jira
JIRA_LOGIN = os.getenv("JIRA_LOGIN")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")

# ============== МОНИТОРИНГ НАСТРОЙКИ ==============
# Интервал проверки новых задач (в секундах)
# 60 = каждую минуту, 300 = каждые 5 минут
CHECK_INTERVAL = 300


# Интервал напоминаний (секунды)
REMINDER_INTERVAL = 300  # 5 минут

# Название колонки которую отслеживаем
MONITORED_COLUMN = "Ожидают тестирования"

# ============== СООБЩЕНИЯ ==============
# Текст уведомления о новых задачах
NOTIFICATION_TEMPLATE = """🔔 Новые задачи на тестирование!

📈 Добавлено: {difference} задач(и)
📊 Всего в колонке: {total_count}
📅 Время: {timestamp}"""

# Сообщение при запуске бота
STARTUP_MESSAGE = "🤖 Бот запущен! Мониторинг активен."

# ============== ОТЛАДКА ==============
# Включить подробные логи в консоли (True/False)
DEBUG_MODE = True

# Показывать статус каждой проверки
SHOW_CHECK_STATUS = True

