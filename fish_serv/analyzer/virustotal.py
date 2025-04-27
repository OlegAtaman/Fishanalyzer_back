import requests
import time
import os

# from ..keys import VIRUSTOTAL_KEY

VT_BASE = 'https://www.virustotal.com/api/v3'


def scan_link(url):
    headers = {
        "x-apikey": "afe50b9fc0d8ff727a7d3b45f9530f81962b1f460073395ae238bb9bb63c28dd"
    }

    print(f"[→] Відправка посилання: {url}")

    # Потрібно передавати як form-data (не url=...)
    response = requests.post(f"{VT_BASE}/urls", data={"url": url}, headers=headers)

    if response.status_code == 200:
        analysis_id = response.json()["data"]["id"]
        print(f"[✓] Посилання відправлене, ID аналізу: {analysis_id}")
        return analysis_id
    else:
        print("[✗] Помилка при відправленні:", response.text)
        return None
    

def get_url_scan_result(analysis_id):
    headers = {
        "x-apikey": "afe50b9fc0d8ff727a7d3b45f9530f81962b1f460073395ae238bb9bb63c28dd"
    }

    url = f"{VT_BASE}/analyses/{analysis_id}"
    print(f"[…] Отримую результати для {analysis_id}...")

    # Чекаємо результат
    for _ in range(150):
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data["data"]["attributes"]["status"]
        if status == "completed":
            stats = data["data"]["attributes"]["stats"]
            print(f"[✓] Результат: {stats}")
            return stats
        time.sleep(2)

    print("[✗] Час очікування перевищено")
    return None

def scan_file(filepath):
    headers = {
        "x-apikey": "afe50b9fc0d8ff727a7d3b45f9530f81962b1f460073395ae238bb9bb63c28dd"
    }

    normalized_path = os.path.normpath(filepath)

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


def get_scan_result(analysis_id):
    headers = {
        "x-apikey": "afe50b9fc0d8ff727a7d3b45f9530f81962b1f460073395ae238bb9bb63c28dd"
    }

    url = f"{VT_BASE}/analyses/{analysis_id}"
    print(f"[…] Отримую результати для {analysis_id}...")

    # Чекаємо результат
    for _ in range(150):
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data["data"]["attributes"]["status"]
        if status == "completed":
            stats = data["data"]["attributes"]["stats"]
            print(f"[✓] Результат: {stats}")
            return stats
        time.sleep(2)

    print("[✗] Час очікування перевищено")
    return None
