# ==============================================
# ОБРАБОТЧИКИ КОМАНД TELEGRAM БОТА
# ==============================================
# Этот файл содержит все функции для обработки команд и кнопок бота
# Каждая функция отвечает за определенное действие пользователя

from telebot import types
from get_desk_api import url, get_column_count_task, get_desk_api
from config import DEBUG_MODE
from datetime import datetime
import time  # Добавлен импорт time

def setup_handlers(bot):
    """
    Главная функция - настраивает все обработчики для бота
    Вызывается один раз при запуске из main.py
    """
    
    # ============== КОМАНДА /START ==============
    @bot.message_handler(commands=['start'])
    def start_message(message):
        """
        Обрабатывает команду /start
        Показывает пользователю кнопки с доступными досками
        """
        if DEBUG_MODE:
            print(f"👤 Пользователь {message.chat.id} запустил бота")
        
        # Создаем клавиатуру с кнопками
        markup = types.InlineKeyboardMarkup()
        
        # Добавляем кнопку для каждой доски из конфига API
        for board_name in url.keys():
            board_button = types.InlineKeyboardButton(
                text=board_name,  # Текст на кнопке
                callback_data=board_name  # Данные для обработки нажатия
            )
            markup.add(board_button)
        
        # Отправляем сообщение с кнопками
        bot.send_message(
            message.chat.id,
            "Выберите доску для просмотра:",
            reply_markup=markup
        )

    # ============== НАЖАТИЕ НА ДОСКУ ==============
    @bot.callback_query_handler(func=lambda call: call.data in url.keys())
    def handle_board_selection(call):
        """
        Обрабатывает нажатие на кнопку доски (например, ARM_QA)
        Показывает колонки с количеством задач в каждой
        """
        if DEBUG_MODE:
            print(f"📋 Выбрана доска: {call.data}")
        
        try:
            # Получаем данные с API
            response = get_desk_api()
            if response.status_code != 200:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка получения данных с сервера"
                )
                return
            
            response_data = response.json()
            markup = types.InlineKeyboardMarkup()
            
            # Создаем кнопку для каждой колонки
            for column_data in response_data['columnsData']['columns']:
                column_name = column_data['name']
                task_count = int(column_data['statisticsFieldValue'])
                
                # Текст кнопки: "Название колонки X задач(а)"
                button_text = f"{column_name} ({task_count} задач)"
                
                column_button = types.InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"column_{column_name}"
                )
                markup.add(column_button)
            
            # Обновляем сообщение с новыми кнопками
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📂 Выберите колонку для просмотра задач:",
                reply_markup=markup
            )
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка при получении колонок: {e}")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Произошла ошибка при загрузке данных"
            )

    # ============== НАЖАТИЕ НА КОЛОНКУ ==============
    @bot.callback_query_handler(func=lambda call: call.data.startswith("column_"))
    def handle_column_selection(call):
        """
        Обрабатывает нажатие на кнопку колонки
        Показывает список всех задач из выбранной колонки
        """
        # Извлекаем название колонки из данных кнопки
        column_name = call.data.replace("column_", "")
        
        if DEBUG_MODE:
            print(f"📂 Выбрана колонка: {column_name}")
        
        try:
            # Получаем задачи из выбранной колонки
            tasks_text = get_column_count_task(selected_column=column_name)
            
            # Создаем кнопку "Назад"
            markup = types.InlineKeyboardMarkup()
            back_button = types.InlineKeyboardButton(
                text="⬅️ Назад к колонкам",
                callback_data="back_to_columns"
            )
            markup.add(back_button)
            
            # Показываем список задач
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=tasks_text,
                reply_markup=markup
            )
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка при получении задач: {e}")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Ошибка при загрузке задач"
            )

    # ============== ПЕРЕХОД В JIRA ИЗ УВЕДОМЛЕНИЙ ==============
    @bot.callback_query_handler(func=lambda call: call.data.startswith("task_"))
    def handle_task_view(call):
        """
        Обрабатывает клик по задаче:
        - Из уведомлений: НЕ ИСПОЛЬЗУЕТСЯ (убрали кнопки задач)
        - Из колонок: показывает детали
        """
        # Это обычная задача из колонки - показываем детали как раньше
        task_key = call.data.replace("task_", "")
        
        if DEBUG_MODE:
            print(f"🔍 Просмотр деталей задачи: {task_key}")
        
        try:
            # Получаем детали задачи из API
            task_details = get_task_details_from_api(task_key)
            
            if task_details:
                details_text = f"🔹 {task_details['key']} — {task_details['summary']}\n\n"
                details_text += f"👤 Исполнитель: {task_details.get('assignee', 'не назначен')}\n"
                
                # Если есть описание - показываем его
                if task_details.get('description'):
                    desc = task_details['description'][:500]
                    if len(task_details['description']) > 500:
                        desc += "..."
                    details_text += f"\n📝 Описание:\n{desc}"
            else:
                details_text = f"❌ Не удалось загрузить данные задачи {task_key}"
            
            # Кнопка возврата к колонкам
            markup = types.InlineKeyboardMarkup()
            back_button = types.InlineKeyboardButton(
                text="⬅️ Назад к колонкам", 
                callback_data="back_to_columns"
            )
            markup.add(back_button)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=details_text,
                reply_markup=markup
            )
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка просмотра задачи: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка загрузки задачи")

    # ============== ВОЗВРАТ К НАПОМИНАНИЮ ==============
    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_reminder_"))
    def handle_back_to_reminder(call):
        """
        Возвращает к исходному сообщению с напоминанием
        """
        reminder_id = call.data.replace("back_to_reminder_", "")
        
        if DEBUG_MODE:
            print(f"⬅️ Возврат к напоминанию {reminder_id}")
        
        try:
            # Безопасный импорт функций из monitor.py
            try:
                from monitor import active_reminders, reminder_readers, find_monitored_column
            except ImportError as e:
                if DEBUG_MODE:
                    print(f"❌ Ошибка импорта из monitor.py: {e}")
                bot.answer_callback_query(call.id, "❌ Ошибка системы")
                return
            
            # Проверяем что напоминание еще активно
            if reminder_id not in active_reminders or not active_reminders[reminder_id]['active']:
                bot.answer_callback_query(call.id, "❌ Напоминание больше не активно")
                return
            
            # Получаем актуальные данные задач
            response = get_desk_api()
            if not response or response.status_code != 200:
                bot.answer_callback_query(call.id, "❌ Ошибка получения данных")
                return
            
            current_data = response.json()
            target_column = find_monitored_column(current_data)
            
            if not target_column:
                bot.answer_callback_query(call.id, "❌ Колонка не найдена")
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
            
            # Формируем сообщение напоминания заново
            elapsed_minutes = int((time.time() - active_reminders[reminder_id]['start_time']) / 60)
            
            message = f"⚠️ Возьмите задачу в работу!\n\n"
            message += f"Задачи ожидают тестирования уже {elapsed_minutes} минут:\n"
            
            for task in still_waiting_tasks:
                message += f"📋 {task['key']} - {task['summary']}\n"
            
            # Добавляем информацию о прочитавших если есть
            if reminder_id in reminder_readers and reminder_readers[reminder_id]:
                readers_list = ", ".join(reminder_readers[reminder_id])
                message += f"\n✅ Прочитали: {readers_list}"
            
            # Создаем кнопки
            markup = types.InlineKeyboardMarkup()
            
            for task in still_waiting_tasks:
                task_text = task['summary'][:40] + "..." if len(task['summary']) > 40 else task['summary']
                task_button = types.InlineKeyboardButton(
                    text=f"📋 {task['key']} - {task_text}",
                    callback_data=f"task_{task['key']}_from_reminder_{reminder_id}"
                )
                markup.add(task_button)
            
            # Кнопки "Прочитано" и "Удалить"
            read_button = types.InlineKeyboardButton(
                text="✅ Прочитано",
                callback_data=f"read_{reminder_id}"
            )
            delete_button = types.InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_{reminder_id}"
            )
            markup.add(read_button, delete_button)
            
            # Обновляем сообщение
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=message,
                reply_markup=markup
            )
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка возврата к напоминанию: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка возврата")

    # ============== КНОПКА "НАЗАД" ==============
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_columns")
    def handle_back_button(call):
        """
        Обрабатывает нажатие кнопки "Назад к колонкам"
        Возвращает пользователя к списку колонок
        """
        if DEBUG_MODE:
            print("⬅️ Возврат к списку колонок")
        
        # Просто вызываем функцию показа колонок
        handle_board_selection(call)

    # ============== КНОПКА "ВЗЯЛ ЗАДАЧУ" ==============
    @bot.callback_query_handler(func=lambda call: call.data.startswith("take_"))
    def handle_take_task(call):
        """Обрабатывает нажатие кнопки 'Взял [номер задачи]' в напоминании"""
        # Парсим: take_UGC-8006_reminder_abc123
        callback_parts = call.data.replace("take_", "").split("_reminder_")
        task_key = callback_parts[0]
        reminder_id = callback_parts[1]
        
        if DEBUG_MODE:
            print(f"💼 Пользователь взял задачу {task_key} из напоминания {reminder_id}")
        
        try:
            # Получаем информацию о пользователе
            user_name = call.from_user.first_name or "Пользователь"
            current_time = datetime.now().strftime("%H:%M")
            
            # Безопасный импорт функций из monitor.py
            try:
                from monitor import active_reminders, reminder_readers, find_monitored_column, stop_reminder
            except ImportError as e:
                if DEBUG_MODE:
                    print(f"❌ Ошибка импорта из monitor.py: {e}")
                bot.answer_callback_query(call.id, "❌ Ошибка системы")
                return
            
            # Проверяем что напоминание еще активно
            if reminder_id not in active_reminders or not active_reminders[reminder_id]['active']:
                bot.answer_callback_query(call.id, "❌ Напоминание больше не активно")
                return
            
            # Инициализируем структуру для хранения взятых задач
            if reminder_id not in reminder_readers:
                reminder_readers[reminder_id] = {}
            
            # Проверяем не взял ли кто-то уже эту задачу
            if task_key in reminder_readers[reminder_id]:
                existing_taker = reminder_readers[reminder_id][task_key]
                bot.answer_callback_query(call.id, f"⚠️ Задачу уже взял {existing_taker}")
                return
            
            # Отмечаем что пользователь взял эту задачу
            reminder_readers[reminder_id][task_key] = f"{user_name} ({current_time})"
            
            # Формируем ссылку на задачу в Jira и отправляем
            jira_url = f"https://jira.zxz.su/browse/{task_key}"
            bot.send_message(
                call.message.chat.id,
                f"🔗 **{task_key}** - открыть в Jira:\n{jira_url}",
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            
            # Показываем подтверждение
            bot.answer_callback_query(call.id, f"💼 Взяли задачу {task_key}!")
            
            # Получаем актуальные данные задач для обновления сообщения
            response = get_desk_api()
            if not response or response.status_code != 200:
                if DEBUG_MODE:
                    print(f"❌ Ошибка получения данных для обновления напоминания {reminder_id}")
                return
            
            current_data = response.json()
            target_column = find_monitored_column(current_data)
            
            if not target_column:
                if DEBUG_MODE:
                    print(f"❌ Колонка не найдена для напоминания {reminder_id}")
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
            
            # Проверяем все ли задачи взяты
            all_tasks_taken = all(
                task['key'] in reminder_readers[reminder_id] 
                for task in still_waiting_tasks
            )
            
            if all_tasks_taken:
                # Все задачи взяты - останавливаем напоминания
                stop_reminder(reminder_id)
                if DEBUG_MODE:
                    print(f"🛑 Все задачи взяты - напоминание {reminder_id} остановлено")
            
            # Формируем обновленное сообщение
            elapsed_minutes = int((time.time() - active_reminders[reminder_id]['start_time']) / 60)
            
            message = f"⚠️ Возьмите задачу в работу!\n\n"
            message += f"Задачи ожидают тестирования уже {elapsed_minutes} минут:\n"
            
            for task in still_waiting_tasks:
                message += f"📋 {task['key']} - {task['summary']}\n"
            
            # Добавляем информацию о взятых задачах
            if reminder_readers[reminder_id]:
                message += f"\n💼 Взяли в работу:\n"
                for taken_task, taker in reminder_readers[reminder_id].items():
                    message += f"- {taken_task}: {taker}\n"
            
            # Создаем кнопки только для НЕ взятых задач
            markup = types.InlineKeyboardMarkup()
            
            for task in still_waiting_tasks:
                if task['key'] not in reminder_readers[reminder_id]:
                    # Задача еще не взята - показываем кнопку
                    task_text = task['summary'][:20] + "..." if len(task['summary']) > 20 else task['summary']
                    take_button = types.InlineKeyboardButton(
                        text=f"💼 Взять {task['key']}",
                        callback_data=f"take_{task['key']}_reminder_{reminder_id}"
                    )
                    markup.add(take_button)
            
            # Кнопка "Удалить" остается всегда
            delete_button = types.InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_{reminder_id}"
            )
            markup.add(delete_button)
            
            # Обновляем сообщение
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=message,
                reply_markup=markup
            )
            
            if DEBUG_MODE:
                print(f"✅ Напоминание {reminder_id} обновлено - {user_name} взял {task_key}")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка при обработке взятия задачи {task_key}: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при обработке")

    # ============== КНОПКА "УДАЛИТЬ УВЕДОМЛЕНИЕ" ==============
    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
    def handle_delete_reminder(call):
        """Обрабатывает нажатие кнопки 'Удалить' в напоминании"""
        reminder_id = call.data.replace("delete_", "")
        
        if DEBUG_MODE:
            print(f"🗑️ Пользователь нажал 'Удалить' для напоминания {reminder_id}")
        
        # Показываем подтверждение
        bot.answer_callback_query(call.id, "🗑️ Уведомление удалено!")
        
        try:
            # Безопасный импорт функций из monitor.py
            try:
                from monitor import stop_reminder, active_reminders
            except ImportError as e:
                if DEBUG_MODE:
                    print(f"❌ Ошибка импорта из monitor.py: {e}")
                return
            
            # Останавливаем напоминание
            stop_reminder(reminder_id)
            
            # Получаем информацию о пользователе для логирования
            user_name = call.from_user.first_name or "Пользователь"
            
            # Удаляем сообщение полностью
            bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            
            if DEBUG_MODE:
                print(f"🗑️ Напоминание {reminder_id} удалено пользователем {user_name}")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка при удалении напоминания {reminder_id}: {e}")
            # Если не получилось удалить - показываем ошибку
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка при удалении уведомления"
                )
            except:
                pass

    # ============== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ==============
    def get_task_details_from_api(task_key):
        """
        Получает детали задачи из API Jira
        
        Args:
            task_key: ключ задачи (например UGC-7913)
            
        Returns:
            dict: данные задачи или None если не найдена
        """
        try:
            # Получаем данные из API
            response = get_desk_api()
            if response and response.status_code == 200:
                api_data = response.json()
                
                # Ищем задачу среди всех задач
                for issue in api_data['issuesData']['issues']:
                    if issue['key'] == task_key:
                        return {
                            'key': issue['key'],
                            'summary': issue['summary'],
                            'assignee': issue.get('assigneeName', 'не назначен'),
                            'description': issue.get('description', 'Описание отсутствует')
                        }
            
            return None
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Ошибка получения деталей задачи {task_key}: {e}")
            return None

    if DEBUG_MODE:
        print("✅ Обработчики команд настроены")