import re
import json
from datetime import datetime

def extract_cookies_from_curl(curl_command):
    # Тот же код извлечения cookies
    cookie_pattern = r'-b\s+[\'"](.+?)[\'"]|--cookie\s+[\'"](.+?)[\'"]'
    cookie_match = re.search(cookie_pattern, curl_command)
    
    if not cookie_match:
        return {}
    
    cookie_str = cookie_match.group(1) if cookie_match.group(1) else cookie_match.group(2)
    
    cookies = {}
    for cookie in cookie_str.split(';'):
        if not cookie.strip():
            continue
        
        parts = cookie.strip().split('=', 1)
        if len(parts) == 2:
            key, value = parts
            cookies[key.strip()] = value.strip()
    
    return cookies

# Название файла с curl запросом
curl_file = input("Название файла curl: ")

try:
    with open(curl_file, 'r', encoding='utf-8') as f:
        curl_command = f.read()
    
    cookies = extract_cookies_from_curl(curl_command)
    
    if not cookies:
        print("В curl-команде не найдены cookies.")
    else:
        output_file = "cookies.json"
        data = {
            "cookies": cookies
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Сохранено {len(cookies)} cookie в файл {output_file}")
except Exception as e:
    print(f"Ошибка: {e}")

