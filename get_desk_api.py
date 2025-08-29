import requests
import json
import os
from dotenv import load_dotenv
from cookie_manager import refresh_cookies_on_401

# Загружаем переменные окружения
load_dotenv()

# Получаем URL из переменных окружения
url = {
    "ARM_QA": os.getenv("JIRA_API_ARM_QA")
}

def get_desk_api():
    """
    Получает данные из Jira API с автоматическим обновлением куков при 401 ошибке
    """
    try:
        # Проверяем существование файла
        try:
            with open('cookies.json', "r") as cookie_file:
                content = cookie_file.read().strip()
                
                # Проверяем что файл не пустой
                if not content:
                    print("⚠️ Файл cookies.json пустой - создаю новые куки...")
                    if refresh_cookies_on_401():
                        return get_desk_api()  # Рекурсивный вызов после создания куков
                    return None
                
                # Парсим JSON
                data = json.loads(content)
                if not data.get('cookies') or not isinstance(data['cookies'], dict):
                    print("⚠️ Некорректная структура cookies.json - создаю новые куки...")
                    if refresh_cookies_on_401():
                        return get_desk_api()  # Рекурсивный вызов после создания куков
                    return None
                
                cookies = data['cookies']
                
                # Проверяем что есть хотя бы один важный кук
                important_cookies = ['JSESSIONID', 'seraph.rememberme.cookie', 'atlassian.xsrf.token']
                if not any(cookie in cookies for cookie in important_cookies):
                    print("⚠️ Отсутствуют важные куки - создаю новые куки...")
                    if refresh_cookies_on_401():
                        return get_desk_api()  # Рекурсивный вызов после создания куков
                    return None
                    
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Ошибка парсинга cookies.json: {e} - создаю новые куки...")
            if refresh_cookies_on_401():
                return get_desk_api()  # Рекурсивный вызов после создания куков
            return None
        
        # Выполняем запрос
        response = requests.get(url=url["ARM_QA"], cookies=cookies)
        
        # Проверяем статус ответа
        print("Статус:", response.status_code)
        
        # Если получена 401 ошибка - обновляем куки и повторяем запрос
        if response.status_code == 401:
            print("🔄 Получена 401 ошибка - обновляю куки...")
            
            # Пытаемся обновить куки
            if refresh_cookies_on_401():
                # Читаем обновленные куки
                with open('cookies.json', "r") as cookie_file:
                    data = json.load(cookie_file)
                    cookies = data['cookies']
                
                # Повторяем запрос с новыми куками
                response = requests.get(url=url["ARM_QA"], cookies=cookies)
                print(f"🔄 Повторный запрос - статус: {response.status_code}")
            else:
                print("❌ Не удалось обновить куки")
        
        return response
        
    except FileNotFoundError:
        print("❌ Файл cookies.json не найден - создаю новые куки...")
        # Пытаемся создать куки с нуля
        if refresh_cookies_on_401():
            return get_desk_api()  # Рекурсивный вызов после создания куков
        return None
    except Exception as e:
        print(f"❌ Ошибка в get_desk_api: {e}")
        return None

#получаем по доске колонки и количество задач в них
def get_column_count_task(selected_column=None, names_only=False):
    try:
        response = get_desk_api()
        
        # Проверяем что ответ получен и успешен
        if not response or response.status_code != 200:
            return "❌ Ошибка получения данных с сервера"
        
        response_json = response.json()
        
        if names_only:
            columns = []
            for column in response_json['columnsData']['columns']:
                columns.append(column['name'])
            return columns
        
        result = ""
        for column in response_json['columnsData']['columns']:
            name_column = column['name']
            task_in_desk = column['statisticsFieldValue']
            
            if selected_column and name_column != selected_column:
                continue
                
            result += f'на доске: {name_column} - {int(task_in_desk)} задач(a)\n'
            statusIDs = column['statusIds']
            count = 0
            
            for issue in response_json['issuesData']['issues']:
                if issue['statusId'] in statusIDs:
                    count += 1
                    result += f"{count:>2}. [{issue['key']}] {issue['summary']} (👤 {issue.get('assigneeName', 'не назначен')})\n"
            
            if count == 0:
                result += "Нет задач в этой колонке.\n"
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка в get_column_count_task: {e}")
        return "❌ Ошибка обработки данных"

