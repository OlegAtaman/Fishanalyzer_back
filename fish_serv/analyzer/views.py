import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import UploadedFile, Rule, Email
from .functions import write_settings, read_settings
from .serializers import UploadedFileSerializer, serialize_rule
from .parser import parse_eml


# Функція для завантаження листа на аналіз через посилання
@api_view(["POST"])
def upload_email(request):
    serializer = UploadedFileSerializer(data=request.data)
    if serializer.is_valid():
        file_record = serializer.save()
        parse_eml(file_record) # Аналізуємо лист
        return Response({"id": file_record.id}, status=status.HTTP_201_CREATED) # Отримуємо id листа
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Функція для отримання інформації про завантажений на аналіз лист
@api_view(["GET"])
def get_risk_score(request, pk):
    try:
        file = UploadedFile.objects.get(pk=pk)
    except UploadedFile.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UploadedFileSerializer(file)
    return Response(serializer.data) # Повертає інформацію про лист


# Функція головної сторінки програми
def index(request):

    # Якщо надіслано лист на аналіз
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"] # Зберігаємо лист
        file_record = UploadedFile.objects.create(
            file=uploaded_file, status="analyzing"
        )

        parse_eml(file_record) # Аналізуємо лист

        return redirect("index")

    # Якщо метод GET - завантажємо всі листи і виводимо на головну сторінку
    files = UploadedFile.objects.order_by("-id")
    files_json = [{"id": f.id} for f in files]

    return render(
        request, "analyzer/index.html", {"files": files, "files_json": files_json}
    )


# Функція для отримання статусу листа
# Якщо статус став "done", то за допомогою JavaScript буде динамічно змінено його на головній сторінці
def get_file_status(request, file_id):
    try:
        file = UploadedFile.objects.get(id=file_id)
        return JsonResponse({"status": file.status, "risk_score": file.risk_score})
    except UploadedFile.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


# Функція для сторінки з налаштуваннями
@csrf_exempt
def firewall_settings(request):
    # Якщо метод GET, то ми виводимо всі налаштування
    if request.method == "GET":
        rules = Rule.objects.all().order_by("priority") # Читаємо правила
        settings_data = read_settings() # Читаємо налаштування
        print(settings_data)
        return render(
            request,
            "analyzer/settings.html",
            {
                "rules": [
                    {
                        "id": rule.id,
                        "recipient": "\n".join(
                            email.email for email in rule.recipient.all()
                        ),
                        "sender": "\n".join(email.email for email in rule.sender.all()),
                        "action": rule.action,
                        "priority": rule.priority,
                    }
                    for rule in rules
                ],
                "save_drop": settings_data["save_drop"],
                "redirect_to_sec": settings_data["redirect_to_sec"],
                "sec_email": settings_data["sec_email"],
            },
        )

    # Метод POST для створення правила
    elif request.method == "POST":
        data = json.loads(request.body)

        # Для всіх адрес створюємо об'єкти типу Email
        def get_email_objects(emails_str):
            emails = [e.strip() for e in emails_str.split(";") if e.strip()]
            return [Email.objects.get_or_create(email=e)[0] for e in emails]

        # Робимо це для отримувачів і відправників
        recipient_emails = get_email_objects(data.get("recipient", "*"))
        sender_emails = get_email_objects(data.get("sender", "*"))

        # Створюємо правило та підключаємо списки відправників і отримувачів
        rule = Rule.objects.create(
            action=data.get("action", "check"), priority=data.get("priority", 100)
        )
        rule.recipient.set(recipient_emails)
        rule.sender.set(sender_emails)

        # Записуємо у файл з налаштуваннями, що правила оновились
        # Це необхідно для оновлення їх на SMTP проксі
        data = read_settings()
        write_settings(
            {
                "rules_update": True,
                "settings_update": data.get("settings_update"),
                "save_drop": data.get("save_drop"),
                "redirect_to_sec": data.get("redirect_to_sec"),
                "sec_email": data.get("sec_email", ""),
            }
        )

        return JsonResponse(
            {
                "id": rule.id,
                "recipient": ";".join(e.email for e in recipient_emails),
                "sender": ";".join(e.email for e in sender_emails),
                "action": rule.action,
                "priority": rule.priority,
            }
        )

    # Функція для видалення правила
    elif request.method == "DELETE":
        data = json.loads(request.body)
        Rule.objects.filter(id=data["id"]).exclude(priority=10000).delete()
        # Також оновлюємо налаштування
        data = read_settings()
        write_settings(
            {
                "rules_update": True,
                "settings_update": data.get("settings_update"),
                "save_drop": data.get("save_drop"),
                "redirect_to_sec": data.get("redirect_to_sec"),
                "sec_email": data.get("sec_email", ""),
            }
        )
        return JsonResponse({"status": "deleted"})

    # Функція оновлення налаштування SMTP проксі
    elif request.method == "PUT":
        data = json.loads(request.body) # Зчитуємо дані із запиту
        # Оновлюємо дані в налаштуваннях
        write_settings(
            {
                "rules_update": read_settings().get("rules_update"),
                "settings_update": True,
                "save_drop": data.get("save_drop") == True,
                "redirect_to_sec": data.get("redirect_to_sec") == True,
                "sec_email": data.get("sec_email", ""),
            }
        )
        return JsonResponse({"status": "settings_saved"})


# Функція для отримання SMTP проксі сервером правил
@csrf_exempt
def check_rules_update(request):
    settings = read_settings()
    rules = Rule.objects.all().order_by("priority")
    # Якщо правила отримуються вперше - замінюємо значення змінної RULES_UPDT на False
    # Це необхідно для оптимізаціївитрати ресурсів серверу.
    # Якщо правила не змінені - немає необхідності їх знову обробляти
    if settings.get("rules_update", False) == True:
        settings["rules_update"] = False
        write_settings(settings) 
        return JsonResponse(
            {"updated": True, "rules": [serialize_rule(r) for r in rules]}
        )
    else:
    # Якщо правила отримуються не вперше - просто даэмо правила (на випадок першого налаштування)
        return JsonResponse(
            {"updated": False, "rules": [serialize_rule(r) for r in rules]}
        )


# Функція для отримання SMTP проксі сервером налаштувань
# Функція працює аналогічно до попередньої, тільки дані отримуються з лише з файлу
@csrf_exempt
def check_settings_update(request):
    settings = read_settings()
    ret_settings = {
        "SAVE_DROP": settings.get("save_drop", False),
        "REDIRECT_TO_SEC": settings.get("redirect_to_sec", False),
        "SEC_EMAIL": settings.get("sec_email", ""),
    }
    if settings.get("settings_update", False) == True:
        settings["settings_update"] = False
        write_settings(settings)
        return JsonResponse({"updated": True, "settings": ret_settings})
    else:
        return JsonResponse({"updated": False, "settings": ret_settings})
