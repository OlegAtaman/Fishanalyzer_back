import os
import re
import threading
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import Q

from .models import UploadedFile, Link, Attachment
from .virustotal import scan_file, get_scan_result, scan_link, get_url_scan_result


# Функція перевіря чи аналіз всіх вкладень та посилань в листі завершено
# Якщо так - присвоює значення "done" всьому листу (Аналіз листа завершено)
def check_if_analysis_done(email: UploadedFile):
    all_files_done = not email.attachments.filter(~Q(status="done")).exists()
    all_links_done = not email.links.filter(~Q(status="done")).exists()

    email.status = "done" if all_files_done and all_links_done else "analyzing"
    email.save()


# Функція для аналізу файлу через Virustotal окремим потоком
def async_scan_file_and_update_risk(filepath, attachment):
    def task():
        # Файл відправляється на аналіз, отримуєтсья id аналізу
        analysis_id = scan_file(filepath)
        if analysis_id:
            # Отримується резульат аналізу - може зайняти час, тому окремим потоком
            result = get_scan_result(analysis_id)
            if result:
                # Присвоюємо оцінку ризику вкладенню
                attachment.risk_score = result.get("malicious")
                attachment.status = "done"
                attachment.save()
                print(
                    f"[✓] Оновлено risk_score для файла: {attachment.filename} → {attachment.risk_score}"
                )
                
                # Якщо оціка ризику вкладення більша за оцінку ризику листа - оновлюємо оцінку ризику листа
                email = attachment.email
                if email.risk_score < attachment.risk_score:
                    email.risk_score = attachment.risk_score

                check_if_analysis_done(email)

    threading.Thread(target=task).start()


# Функція для аналізу посилання через Virustotal - працює аналогчно до функції вище
def async_scan_url_and_update_risk(link_obj):
    def task():
        analysis_id = scan_link(link_obj.url)
        if analysis_id:
            result = get_url_scan_result(analysis_id)
            if result:
                link_obj.risk_score = result.get("malicious")
                link_obj.status = "done"
                link_obj.save()
                print(
                    f"[✓] Оновлено risk_score для URL: {link_obj.url} → {link_obj.risk_score}"
                )

                email = link_obj.email
                if email.risk_score < link_obj.risk_score:
                    email.risk_score = link_obj.risk_score

                check_if_analysis_done(email)

    threading.Thread(target=task).start()


# Основна функція для обробки листа .eml
def parse_eml(uploaded: UploadedFile):
    # Якщо ми вже аналізували такі листи чи вкладення - завершуємо аналіз
    if uploaded.links.exists() or uploaded.attachments.exists():
        print(f"[!] Email ID {uploaded.id} вже оброблений — скасовано.")
        return

    uploaded.status = "analyzing"
    uploaded.save()

    # Відкриваємо файл та зчитуємо його у змінну
    eml_path = uploaded.file.path
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    links = set()

    # Парсимо файл та шукаємо посилання
    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == "text/plain":
            body = part.get_content()
            urls = re.findall(r"https?://\S+", body)
            links.update(urls)

        elif content_type == "text/html":
            html = part.get_content()
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                links.add(a["href"])

    # Не аналізуємо лист якщо у ньому немає посилань чи вкладень
    if len(links) == 0 and len(list(msg.iter_attachments())) == 0:
        uploaded.status = "done"
        uploaded.save()
        return

    # Зберігаємо посилання як об'єкт у БД
    for url in links:
        link = Link.objects.create(
            email=uploaded, status="analyzing", url=url, risk_score=0
        )
        print(f'[+] Посилання "{url}" додане')
        # Відправляємо на аналіз та оновлюємо ризик посилання і всього листа
        async_scan_url_and_update_risk(link)

    # Проводимо аналіз вкладень
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if not filename:
            continue

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        # Зберігаємо файл для аналізу
        attachments_folder = os.path.join(settings.MEDIA_ROOT, "attachments")
        os.makedirs(attachments_folder, exist_ok=True)

        full_path = os.path.join(attachments_folder, filename)
        relative_path = os.path.join("attachments", filename)

        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(full_path):
            print(f'[!] Файл "{filename}" вже існує, перейменовую...')
            filename = f"{base}_{counter}{ext}"
            full_path = os.path.join(attachments_folder, filename)
            relative_path = os.path.join("attachments", filename)
            counter += 1

        with open(full_path, "wb") as out_file:
            out_file.write(payload)

        # Зберігаємо файл як об'єкт відповідної моделі
        attachment = Attachment.objects.create(
            email=uploaded,
            status="analyzing",
            filename=filename,
            file=relative_path,
            risk_score=0,
        )

        # Аналізуємо файл
        print(f'[+] Файл "{filename}" доданий')
        async_scan_file_and_update_risk(full_path, attachment)

    print(f"[✓] Парсинг завершено для email ID: {uploaded.id}")
