# ==============================================
# КОНФИГУРАЦИЯ ДЛЯ АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИИ JIRA
# ==============================================

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# URL Jira
JIRA_URL = os.getenv("JIRA_URL", "https://jira.zxz.su")

# Данные для входа (из переменных окружения)
JIRA_LOGIN = os.getenv("JIRA_LOGIN")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")

# Проверяем наличие обязательных переменных
if not JIRA_LOGIN or not JIRA_PASSWORD:
    print("❌ ОШИБКА: Отсутствуют учетные данные Jira в переменных окружения")
    print("📋 Проверьте файл .env")
    sys.exit(1)
