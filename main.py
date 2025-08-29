# ==============================================
# ГЛАВНЫЙ ФАЙЛ ПРИЛОЖЕНИЯ
# ==============================================
# Это точка входа в программу - отсюда запускается весь бот
# Импортирует все модули и соединяет их вместе

import telebot
from config import BOT_TOKEN, WORK_CHAT_ID, STARTUP_MESSAGE, DEBUG_MODE
from bot_handlers import setup_handlers
from monitor import start_monitoring 

def main():
    """
    Главная функция приложения
    Настраивает и запускает Telegram бота с системой мониторинга
    """
    
    print("=" * 50)
    print("🤖 JIRA MONITORING TELEGRAM BOT")
    print("=" * 50)
    
    # ============== СОЗДАНИЕ БОТА ==============
    if DEBUG_MODE:
        print("⚙️ Создаю объект Telegram бота...")
    
    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        if DEBUG_MODE:
            print("✅ Бот создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return
    
    # ============== ТЕСТОВОЕ СООБЩЕНИЕ ==============
    """
    if DEBUG_MODE:
        print("📤 Отправляю тестовое сообщение...")
    
    try:
        bot.send_message(WORK_CHAT_ID, STARTUP_MESSAGE)
        if DEBUG_MODE:
            print("✅ Тестовое сообщение отправлено успешно")
    except Exception as e:
        print(f"❌ Ошибка отправки тестового сообщения: {e}")
        print("⚠️ Проверьте права бота в чате и правильность WORK_CHAT_ID")
        return
    """
    # ============== НАСТРОЙКА ОБРАБОТЧИКОВ ==============
    if DEBUG_MODE:
        print("⚙️ Настраиваю обработчики команд...")
    
    try:
        setup_handlers(bot)
        if DEBUG_MODE:
            print("✅ Обработчики команд настроены")
    except Exception as e:
        print(f"❌ Ошибка настройки обработчиков: {e}")
        return
    
    # ============== ЗАПУСК МОНИТОРИНГА ==============
    if DEBUG_MODE:
        print("⚙️ Запускаю систему мониторинга...")
    
    try:
        start_monitoring(bot)
        if DEBUG_MODE:
            print("✅ Система мониторинга запущена")
    except Exception as e:
        print(f"❌ Ошибка запуска мониторинга: {e}")
        return
    
    # ============== ЗАПУСК БОТА ==============
    print("🚀 Бот запущен и готов к работе!")
    print("📋 Доступные команды: /start")
    print("🔍 Мониторинг колонки активен")
    print("⏹️ Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Основной цикл обработки сообщений
        bot.polling(none_stop=True, interval=1, timeout=30)
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки...")
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапустите бота")

def check_config():
    """
    Проверяет корректность конфигурации перед запуском
    
    Returns:
        bool: True если конфигурация корректна
    """
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Не указан токен бота в config.py")
        return False
    
    if not WORK_CHAT_ID:
        print("❌ Не указан ID рабочего чата в config.py")
        return False
    
    return True

if __name__ == "__main__":
    # Проверяем конфигурацию перед запуском
    if check_config():
        main()
    else:
        print("⚠️ Исправьте настройки в файле config.py")
        print("📖 Инструкции по настройке см. в комментариях файла")