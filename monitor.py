# ==============================================
# СИСТЕМА МОНИТОРИНГА ЗАДАЧ JIRA
# ==============================================
# Этот файл отвечает за отслеживание изменений в колонке Jira
# и отправку уведомлений в Telegram чат

import time
import threading
from telebot import types
from get_desk_api import get_desk_api
from config import (
    WORK_CHAT_ID, 
    CHECK_INTERVAL, 
    MONITORED_COLUMN, 
    NOTIFICATION_TEMPLATE,
    DEBUG_MODE,
    SHOW_CHECK_STATUS,
    REMINDER_INTERVAL 
)

# Глобальная переменная для хранения последнего состояния
last_column_state = {}
# Глобальная переменная для активных напоминаний
active_reminders = {}
# Глобальная переменная для хранения кто прочитал напоминания
reminder_readers = {}

def start_monitoring(bot):
    """
    Запускает систему мониторинга в отдельном потоке
    
    Args:
        bot: объект Telegram бота для отправки сообщений
    """
    
    def monitor_loop():
        """
        Основной цикл мониторинга
        Выполняется в отдельном потоке каждые CHECK_INTERVAL секунд
        """
        global last_column_state
        
        if DEBUG_MODE:
            print(f"🔍 Мониторинг колонки '{MONITORED_COLUMN}' запущен")
            print(f"⏱️ Интервал проверки: {CHECK_INTERVAL} секунд")
        
        while True:
            try:
                if SHOW_CHECK_STATUS:
                    print(f"⏰ Проверка в {time.strftime('%H:%M:%S')}")
                
                # Получаем свежие данные из Jira API
                response = get_desk_api()
                
                if response and response.status_code == 200:
                    current_data = response.json()
                    
                    # Ищем нужную колонку среди всех колонок
                    target_column = find_monitored_column(current_data)
                    
                    if target_column:
                        process_column_data(target_column, bot, current_data)
                    else:
                        if DEBUG_MODE:
                            print(f"⚠️ Колонка '{MONITORED_COLUMN}' не найдена")
                else:
                    if DEBUG_MODE:
                        print(f"❌ Ошибка API: статус {response.status_code if response else 'нет ответа'}")
                        
            except Exception as e:
                if DEBUG_MODE:
                    print(f"❌ Ошибка мониторинга: {e}")
            
            # Ждем до следующей проверки
            time.sleep(CHECK_INTERVAL)
    
    # Запускаем мониторинг в отдельном потоке
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    if DEBUG_MODE:
        print("✅ Поток мониторинга запущен")

def find_monitored_column(api_data):
    """
    Находит отслеживаемую колонку в данных API
    
    Args:
        api_data: данные полученные от Jira API
        
    Returns:
        dict: данные колонки или None если не найдена
    """
    for column in api_data['columnsData']['columns']:
        if column['name'] == MONITORED_COLUMN:
            return column
    return None

def process_column_data(column_data, bot, full_api_data):
    """
    Обрабатывает данные колонки и отправляет уведомления при изменениях
    
    Args:
        column_data: данные колонки из API
        bot: объект Telegram бота
        full_api_data: полные данные API для поиска новых задач
    """
    global last_column_state
    
    current_count = int(column_data['statisticsFieldValue'])
    
    if SHOW_CHECK_STATUS:
        print(f"📊 Задач в колонке '{MONITORED_COLUMN}': {current_count}")
    
    # Проверяем есть ли предыдущее состояние
    if MONITORED_COLUMN in last_column_state:
        old_count = last_column_state[MONITORED_COLUMN]
        
        if SHOW_CHECK_STATUS:
            print(f"📈 Было задач: {old_count}")
        
        # Если количество задач увеличилось - отправляем уведомление
        if current_count > old_count:
            # Получаем данные о новых задачах
            new_tasks = get_new_tasks_data(column_data, full_api_data)
            send_notification(bot, old_count, current_count, new_tasks)
            
    else:
        if DEBUG_MODE:
            print("🆕 Первая проверка - устанавливаю базовое значение")
    
    # Обновляем сохраненное состояние
    last_column_state[MONITORED_COLUMN] = current_count

def get_new_tasks_data(column_data, full_api_data):
    """
    Получает данные о задачах из отслеживаемой колонки
    
    Args:
        column_data: данные колонки
        full_api_data: полные данные API
        
    Returns:
        list: список задач с их данными
    """
    tasks = []
    status_ids = column_data['statusIds']
    
    # Проходим по всем задачам и находим те что в нужной колонке
    for issue in full_api_data['issuesData']['issues']:
        if issue['statusId'] in status_ids:
            tasks.append({
                'key': issue['key'],
                'summary': issue['summary'],
                'assignee': issue.get('assigneeName', 'не назначен'),
                'status_id': issue['statusId']
            })
    
    return tasks

def send_notification(bot, old_count, new_count, new_tasks_data=None):
    """
    Отправляет уведомление о новых задачах с кнопками для просмотра
    
    Args:
        bot: объект Telegram бота
        old_count: предыдущее количество задач
        new_count: текущее количество задач
        new_tasks_data: данные о задачах
    """
    difference = new_count - old_count
    timestamp = time.strftime('%H:%M:%S %d.%m.%Y')
    
    # Формируем сообщение из шаблона
    message = NOTIFICATION_TEMPLATE.format(
        difference=difference,
        total_count=new_count,
        timestamp=timestamp
    )
    
    if DEBUG_MODE:
        print(f"🚨 НОВЫЕ ЗАДАЧИ! Отправляю уведомление...")
        print(f"📧 Уведомление: +{difference} задач(и) (всего: {new_count})")
    
    # Создаем кнопки для задач
    markup = types.InlineKeyboardMarkup()
    
    if new_tasks_data:
        # Показываем последние добавленные задачи (максимум 5)
        recent_tasks = new_tasks_data[-difference:] if difference <= len(new_tasks_data) else new_tasks_data[:5]
        
        for task in recent_tasks:
            # Обрезаем длинный текст
            task_text = task['summary'][:40] + "..." if len(task['summary']) > 40 else task['summary']
            
            task_button = types.InlineKeyboardButton(
                text=f"📋 {task['key']} - {task_text}",
                callback_data=f"task_{task['key']}"
            )
            markup.add(task_button)
    
    try:
        # Отправляем уведомление в рабочий чат
        bot.send_message(WORK_CHAT_ID, message, reply_markup=markup if new_tasks_data else None)
         # Запускаем напоминания для новых задач
        if new_tasks_data:
            start_reminder_for_tasks(bot, [task['key'] for task in recent_tasks])
        if DEBUG_MODE:
            print("✅ Уведомление успешно отправлено!")
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка отправки уведомления: {e}")

def get_monitoring_status():
    """
    Возвращает текущий статус мониторинга
    
    Returns:
        dict: информация о состоянии мониторинга
    """
    return {
        'monitored_column': MONITORED_COLUMN,
        'check_interval': CHECK_INTERVAL,
        'last_known_count': last_column_state.get(MONITORED_COLUMN, 0),
        'is_active': True
    }

def start_reminder_for_tasks(bot, task_keys):
    """Запускает напоминания для списка задач"""
    global active_reminders, reminder_readers
    
    import time
    import uuid
    
    # Генерируем уникальный ID для напоминания
    reminder_id = str(uuid.uuid4())[:8]
    
    # Сохраняем информацию о напоминании
    active_reminders[reminder_id] = {
        'task_keys': task_keys,
        'start_time': time.time(),
        'active': True
    }
    
    # Инициализируем список взявших задачи для этого напоминания (словарь: задача -> кто взял)
    reminder_readers[reminder_id] = {}
    
    # Запускаем таймер в отдельном потоке
    def reminder_timer():
        time.sleep(REMINDER_INTERVAL)
        if reminder_id in active_reminders and active_reminders[reminder_id]['active']:
            send_reminder(bot, reminder_id)
    
    reminder_thread = threading.Thread(target=reminder_timer, daemon=True)
    reminder_thread.start()
    
    if DEBUG_MODE:
        print(f"⏰ Запущено напоминание {reminder_id} для {len(task_keys)} задач(и)")

def send_reminder(bot, reminder_id):
    """Отправляет напоминание о задачах"""
    global active_reminders, reminder_readers
    
    if reminder_id not in active_reminders or not active_reminders[reminder_id]['active']:
        return
    
    try:
        # Получаем актуальные данные
        response = get_desk_api()
        if not response or response.status_code != 200:
            return
        
        current_data = response.json()
        
        # Находим колонку "Ожидают тестирования"
        target_column = find_monitored_column(current_data)
        if not target_column:
            return
        
        # Получаем задачи которые всё ещё в колонке
        still_waiting_tasks = []
        status_ids = target_column['statusIds']
        
        for issue in current_data['issuesData']['issues']:
            if (issue['statusId'] in status_ids and 
                issue['key'] in active_reminders[reminder_id]['task_keys']):
                still_waiting_tasks.append({
                    'key': issue['key'],
                    'summary': issue['summary']
                })
        
        # Если есть задачи которые всё ещё ждут
        if still_waiting_tasks:
            elapsed_minutes = int((time.time() - active_reminders[reminder_id]['start_time']) / 60)
            
            message = f"⚠️ Возьмите задачу в работу!\n\n"
            message += f"Задачи ожидают тестирования уже {elapsed_minutes} минут:\n"
            
            # Добавляем список задач в текст сообщения
            for task in still_waiting_tasks:
                message += f"📋 {task['key']} - {task['summary']}\n"
            
            # Добавляем информацию о взятых задачах если есть
            if reminder_id in reminder_readers and reminder_readers[reminder_id]:
                message += f"\n💼 Взяли в работу:\n"
                for task_key, taker in reminder_readers[reminder_id].items():
                    message += f"- {task_key}: {taker}\n"
            
            # Создаем кнопки для каждой задачи отдельно
            markup = types.InlineKeyboardMarkup()
            
            for task in still_waiting_tasks:
                task_text = task['summary'][:20] + "..." if len(task['summary']) > 20 else task['summary']
                take_button = types.InlineKeyboardButton(
                    text=f"💼 Взять {task['key']}",
                    callback_data=f"take_{task['key']}_reminder_{reminder_id}"
                )
                markup.add(take_button)
            
            # Кнопка "Удалить"
            delete_button = types.InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_{reminder_id}"
            )
            markup.add(delete_button)
            
            # Отправляем напоминание
            bot.send_message(WORK_CHAT_ID, message, reply_markup=markup)
            
            if DEBUG_MODE:
                print(f"📤 Отправлено напоминание {reminder_id} для {len(still_waiting_tasks)} задач(и)")
            
            # Запускаем следующий таймер
            def next_reminder():
                time.sleep(REMINDER_INTERVAL)
                if reminder_id in active_reminders and active_reminders[reminder_id]['active']:
                    send_reminder(bot, reminder_id)
            
            reminder_thread = threading.Thread(target=next_reminder, daemon=True)
            reminder_thread.start()
        else:
            # Все задачи ушли из колонки - останавливаем напоминания
            active_reminders[reminder_id]['active'] = False
            if DEBUG_MODE:
                print(f"🛑 Напоминание {reminder_id} остановлено - все задачи взяты в работу")
                
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка отправки напоминания {reminder_id}: {e}")

def add_reader_to_reminder(reminder_id, user_name, user_time):
    """Добавляет пользователя в список прочитавших напоминание"""
    global reminder_readers
    
    if reminder_id not in reminder_readers:
        reminder_readers[reminder_id] = []
    
    # Проверяем что пользователь еще не добавлен
    reader_entry = f"{user_name} ({user_time})"
    if reader_entry not in reminder_readers[reminder_id]:
        reminder_readers[reminder_id].append(reader_entry)
        if DEBUG_MODE:
            print(f"📖 Добавлен читатель {reader_entry} к напоминанию {reminder_id}")

def stop_reminder(reminder_id):
    """Останавливает напоминание"""
    global active_reminders
    
    if reminder_id in active_reminders:
        active_reminders[reminder_id]['active'] = False
        if DEBUG_MODE:
            print(f"🛑 Напоминание {reminder_id} остановлено пользователем")