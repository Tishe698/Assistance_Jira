# ==============================================
# ТЕСТОВЫЙ СКРИПТ ДЛЯ ПРОВЕРКИ ОБНОВЛЕНИЯ КУКОВ
# ==============================================

from cookie_manager import login_and_get_cookies
from get_desk_api import get_desk_api

def test_cookie_update():
    """
    Тестирует автоматическое обновление куков
    """
    print("🧪 Тестирование автоматического обновления куков...")
    
    # Пытаемся получить новые куки
    success = login_and_get_cookies()
    
    if success:
        print("✅ Куки успешно обновлены!")
        
        # Тестируем API запрос
        print("🔍 Тестируем API запрос...")
        response = get_desk_api()
        
        if response and response.status_code == 200:
            print("✅ API запрос успешен!")
            return True
        else:
            print(f"❌ API запрос не удался: статус {response.status_code if response else 'нет ответа'}")
            return False
    else:
        print("❌ Не удалось обновить куки")
        return False

if __name__ == "__main__":
    test_cookie_update()
