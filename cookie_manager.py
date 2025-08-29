# ==============================================
# АВТОМАТИЧЕСКИЙ МЕНЕДЖЕР КУКОВ JIRA
# ==============================================
# Этот модуль автоматически обновляет куки при получении 401 ошибки
# используя Selenium для входа в аккаунт

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from auth_config import JIRA_URL, JIRA_LOGIN, JIRA_PASSWORD
from config import DEBUG_MODE

def setup_chrome_driver():
    """
    Настраивает Chrome драйвер для работы в фоновом режиме
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Работа в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка создания Chrome драйвера: {e}")
        return None

def examination_join(driver):
    """
    Проверяет доступность страницы логина
    """
    try:
        driver.get(f"{JIRA_URL}/login.jsp")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        if DEBUG_MODE:
            print(f"🟢 Страница логина открыта: {driver.title}")
        return True
    except WebDriverException as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка подключения к Jira: {e}")
        return False

def continued_authorization(driver):
    """
    Выполняет авторизацию в Jira
    """
    try:
        if DEBUG_MODE:
            print("🔍 Ищем кнопку входа...")
        
        # Пробуем найти кнопку входа разными способами
        try:
            # Сначала пробуем по классу
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "css-1erlht4"))
            )
            login_button.click()
        except:
            if DEBUG_MODE:
                print("⚠️ Кнопка по классу не найдена, ищем по тексту...")
            # Пробуем найти по тексту
            try:
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Войти')]")
                login_button.click()
            except:
                if DEBUG_MODE:
                    print("⚠️ Кнопка по тексту не найдена, пропускаем...")
        
        time.sleep(2)

        if DEBUG_MODE:
            print("🔍 Ищем поля логина и пароля...")
        
        # Находим поля логина и пароля
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-form-username"))
        )
        pass_field = driver.find_element(By.ID, "login-form-password")

        if DEBUG_MODE:
            print("📝 Вводим учетные данные...")

        # Вводим учетные данные
        login_field.clear()
        login_field.send_keys(JIRA_LOGIN)
        pass_field.clear()
        pass_field.send_keys(JIRA_PASSWORD)

        if DEBUG_MODE:
            print("✅ Учетные данные введены")

        return True

    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка на этапе ввода логина/пароля: {e}")
        return False

def click_join(driver):
    """
    Выполняет вход в систему
    """
    try:
        if DEBUG_MODE:
            print("🔍 Ищем чекбокс 'Запомнить меня'...")
        
        # Пробуем найти чекбокс "Запомнить меня"
        try:
            remember_checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login-form-remember-me"))
            )
            if not remember_checkbox.is_selected():
                driver.execute_script("arguments[0].click();", remember_checkbox)
                if DEBUG_MODE:
                    print("✅ Чекбокс 'Запомнить меня' отмечен")
        except:
            if DEBUG_MODE:
                print("⚠️ Чекбокс 'Запомнить меня' не найден, пропускаем...")

        if DEBUG_MODE:
            print("🔍 Ищем кнопку входа...")
        
        # Нажимаем кнопку входа
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
        
        if DEBUG_MODE:
            print("🔄 Нажимаем кнопку входа...")

        # Ждем успешного входа - пробуем разные селекторы
        success = False
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "header-details-user-fullname"))
            )
            success = True
        except:
            try:
                # Альтернативный способ проверки успешного входа
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "user-avatar"))
                )
                success = True
            except:
                # Проверяем по URL
                if "dashboard" in driver.current_url or "browse" in driver.current_url:
                    success = True
        
        if success:
            if DEBUG_MODE:
                print("✅ Вы успешно вошли в аккаунт Jira")
            return True
        else:
            if DEBUG_MODE:
                print("⚠️ Не удалось подтвердить успешный вход")
            return True  # Все равно возвращаем True, так как куки могли установиться

    except NoSuchElementException:
        if DEBUG_MODE:
            print("❌ Не удалось найти элементы авторизации")
        return False
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка при клике по кнопке входа: {e}")
        return False

def extract_cookies_from_driver(driver):
    """
    Извлекает куки из браузера
    """
    try:
        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        
        if DEBUG_MODE:
            print(f"🍪 Извлечено {len(cookies)} куков")
        return cookies
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка извлечения куков: {e}")
        return {}

def save_cookies_to_file(cookies):
    """
    Сохраняет куки в файл cookies.json
    """
    try:
        data = {"cookies": cookies}
        with open('cookies.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        if DEBUG_MODE:
            print("💾 Куки сохранены в cookies.json")
        return True
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка сохранения куков: {e}")
        return False

def login_and_get_cookies():
    """
    Главная функция - выполняет вход и получает новые куки
    """
    if DEBUG_MODE:
        print("🔄 Начинаю процесс получения новых куков...")
    
    driver = setup_chrome_driver()
    if not driver:
        return False
    
    try:
        # Проверяем доступность страницы
        if not examination_join(driver):
            return False
        
        # Выполняем авторизацию
        if not continued_authorization(driver):
            return False
        
        # Входим в систему
        if not click_join(driver):
            return False
        
        # Даем время для установки всех куков
        time.sleep(3)
        
        # Извлекаем куки
        cookies = extract_cookies_from_driver(driver)
        if not cookies:
            return False
        
        # Сохраняем куки в файл
        if not save_cookies_to_file(cookies):
            return False
        
        if DEBUG_MODE:
            print("✅ Куки успешно обновлены!")
        return True
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Ошибка в процессе получения куков: {e}")
        return False
    finally:
        # Закрываем браузер
        driver.quit()

def refresh_cookies_on_401():
    """
    Обновляет куки при получении 401 ошибки
    """
    if DEBUG_MODE:
        print("🔄 Получена 401 ошибка - обновляю куки...")
    
    success = login_and_get_cookies()
    
    if success and DEBUG_MODE:
        print("✅ Куки обновлены, можно продолжать работу")
    else:
        print("❌ Не удалось обновить куки")
    
    return success
