import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from .config import JIRA_URL, JIRA_LOGIN, JIRA_PASSWORD


def examination_join(driver):
    try:
        driver.get(f"{JIRA_URL}/login.jsp")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        if "Вход в систему" in driver.title:
            print(f"🟢 Страница логина открыта: {driver.title}")
        else:
            print(f"⚠️ Заголовок страницы отличается: {driver.title}")
    except WebDriverException:
        print("❌ Ошибка подключения к Jira")


def continued_authorization(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "css-1erlht4"))
        ).click()
        time.sleep(1)

        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-form-username"))
        )
        pass_field = driver.find_element(By.ID, "login-form-password")

        login_field.clear()
        login_field.send_keys(JIRA_LOGIN)
        pass_field.clear()
        pass_field.send_keys(JIRA_PASSWORD)

    except Exception as e:
        print(f"❌ Ошибка на этапе ввода логина/пароля: {e}")


def click_join(driver):
    try:
        remember_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login-form-remember-me"))
        )
        if not remember_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", remember_checkbox)

        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "header-details-user-fullname"))
        )
        print("✅ Вы успешно вошли в аккаунт Jira")

    except NoSuchElementException:
        print("❌ Не удалось найти элементы авторизации. Возможно, изменился интерфейс Jira.")
    except Exception as e:
        print(f"❌ Ошибка при клике по кнопке входа: {e}")
