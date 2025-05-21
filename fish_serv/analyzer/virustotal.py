import requests
import time
import os
from dotenv import load_dotenv
import os


load_dotenv()
VT_API_KEY = os.getenv("VT_API_KEY")

VT_BASE = "https://www.virustotal.com/api/v3"


# Функція для відправки посилання на аналіз та отримання id 
def scan_link(url):
    headers = {
        "x-apikey": VT_API_KEY
    }

    print(f"[→] Відправка посилання: {url}")

    # Відправляємо на Virustotal посилання
    response = requests.post(f"{VT_BASE}/urls", data={"url": url}, headers=headers)

    if response.status_code == 200:
        analysis_id = response.json()["data"]["id"]
        print(f"[✓] Посилання відправлене, ID аналізу: {analysis_id}")
        return analysis_id
    else:
        print("[✗] Помилка при відправленні:", response.text)
        return None


# Функція для отримання результату аналізу посилання
def get_url_scan_result(analysis_id):
    headers = {
        "x-apikey": VT_API_KEY
    }

    url = f"{VT_BASE}/analyses/{analysis_id}"
    print(f"[…] Отримую результати для {analysis_id}...")

    # Кожні 2 секунди відправляємо посилання на аналіз
    for _ in range(150):
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data["data"]["attributes"]["status"]
        if status == "completed":
            stats = data["data"]["attributes"]["stats"]
            print(f"[✓] Результат: {stats}")
            return stats # Повертаємо результат аналізу
        time.sleep(2) # Чекаємо результат протягом 300 секунд

    print("[✗] Час очікування перевищено")
    return None


# Функція для відправки файла на аналіз та отримання id 
def scan_file(filepath):
    headers = {
        "x-apikey": VT_API_KEY
    }

    normalized_path = os.path.normpath(filepath)

    # Відкриваємо та відправляємо файл
    with open(normalized_path, "rb") as f:
        files = {"file": (os.path.basename(normalized_path), f)}
        response = requests.post(f"{VT_BASE}/files", files=files, headers=headers)

    if response.status_code == 200:
        analysis_id = response.json()["data"]["id"]
        print(f"[✓] Файл відправлений, ID аналізу: {analysis_id}")
        return analysis_id
    else:
        print("[✗] Помилка при відправленні:", response.text)
        return None


# Функція для отримання результату аналізу файлу
def get_scan_result(analysis_id):
    headers = {
        "x-apikey": VT_API_KEY
    }

    url = f"{VT_BASE}/analyses/{analysis_id}"
    print(f"[…] Отримую результати для {analysis_id}...")

    
    # Кожні 2 секунди відправляємо запит на Virustotal 
    for _ in range(150):
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data["data"]["attributes"]["status"]
        if status == "completed":
            stats = data["data"]["attributes"]["stats"]
            print(f"[✓] Результат: {stats}")
            return stats # Повертаємо результат аналізу
        time.sleep(2) # Чекаємо результат протягом 300 секунд

    print("[✗] Час очікування перевищено")
    return None
