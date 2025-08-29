#!/usr/bin/env python3
# ==============================================
# СКРИПТ БЕЗОПАСНОГО ЗАПУСКА БОТА
# ==============================================
# Этот скрипт проверяет, не запущен ли уже бот, и запускает его безопасно

import os
import sys
import signal
import subprocess
import time
import psutil

def kill_existing_bot():
    """
    Останавливает все запущенные экземпляры бота
    """
    print("🔍 Проверяю запущенные экземпляры бота...")
    
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'main.py' in ' '.join(cmdline) and 'python' in ' '.join(cmdline):
                print(f"🛑 Останавливаю процесс {proc.info['pid']}...")
                proc.terminate()
                killed += 1
                time.sleep(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed > 0:
        print(f"✅ Остановлено {killed} экземпляров бота")
    else:
        print("ℹ️ Запущенных экземпляров бота не найдено")
    
    return killed

def signal_handler(signum, frame):
    """
    Обработчик сигналов для корректного завершения
    """
    print("\n⏹️ Получен сигнал остановки...")
    kill_existing_bot()
    print("🛑 Выход из программы")
    sys.exit(0)

def main():
    """
    Главная функция запуска бота
    """
    print("=" * 50)
    print("🤖 JIRA MONITORING TELEGRAM BOT - БЕЗОПАСНЫЙ ЗАПУСК")
    print("=" * 50)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Останавливаем существующие экземпляры
    kill_existing_bot()
    
    # Ждем немного перед запуском
    print("⏳ Ожидание перед запуском...")
    time.sleep(2)
    
    # Проверяем наличие необходимых файлов
    required_files = ['main.py', 'config.py', 'cookie_manager.py', 'auth_config.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Отсутствует необходимый файл: {file}")
            return False
    
    print("🚀 Запускаю бота...")
    
    try:
        # Запускаем бота
        process = subprocess.Popen([
            sys.executable, 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        # Выводим логи в реальном времени
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Ждем завершения процесса
        return_code = process.poll()
        
        if return_code == 0:
            print("✅ Бот завершился успешно")
            return True
        else:
            print(f"❌ Бот завершился с ошибкой (код: {return_code})")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
