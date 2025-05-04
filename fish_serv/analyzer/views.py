from django.shortcuts import render, redirect
from .models import UploadedFile, Rule, Email
from django.http import JsonResponse
from .parser import parse_eml
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UploadedFileSerializer, serialize_rule
from django.views.decorators.csrf import csrf_exempt
from .functions import write_settings, read_settings
import json


@api_view(['POST'])
def upload_email(request):
    serializer = UploadedFileSerializer(data=request.data)
    if serializer.is_valid():
        file_record = serializer.save()
        parse_eml(file_record)
        return Response({'id': file_record.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_risk_score(request, pk):
    try:
        file = UploadedFile.objects.get(pk=pk)
    except UploadedFile.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UploadedFileSerializer(file)
    return Response(serializer.data)


def index(request):
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_record = UploadedFile.objects.create(file=uploaded_file, status='analyzing')
        
        parse_eml(file_record)

        return redirect('index')
    
    files = UploadedFile.objects.order_by('-id')
    files_json = [{"id": f.id} for f in files]


    return render(request, 'analyzer/index.html', {"files": files, "files_json": files_json})

def get_file_status(request, file_id):
    try:
        file = UploadedFile.objects.get(id=file_id)
        return JsonResponse({
            "status": file.status,
            "risk_score": file.risk_score
        })
    except UploadedFile.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


@csrf_exempt
def firewall_settings(request):
    if request.method == 'GET':
        rules = Rule.objects.all().order_by('priority')
        settings_data = read_settings()
        print(settings_data)
        return render(request, 'analyzer/settings.html', {
            'rules': [
                {
                    'id': rule.id,
                    'recipient': '\n'.join(email.email for email in rule.recipient.all()),
                    'sender': '\n'.join(email.email for email in rule.sender.all()),
                    'action': rule.action,
                    'priority': rule.priority
                }
                for rule in rules
            ],
            'save_drop': settings_data['save_drop'],
            'redirect_to_sec': settings_data['redirect_to_sec'],
            'sec_email': settings_data['sec_email'],
        })

    elif request.method == 'POST':
        data = json.loads(request.body)

        # Parse and fetch/create Email objects
        def get_email_objects(emails_str):
            emails = [e.strip() for e in emails_str.split(';') if e.strip()]
            return [Email.objects.get_or_create(email=e)[0] for e in emails]

        recipient_emails = get_email_objects(data.get('recipient', '*'))
        sender_emails = get_email_objects(data.get('sender', '*'))

        rule = Rule.objects.create(
            action=data.get('action', 'check'),
            priority=data.get('priority', 100)
        )
        rule.recipient.set(recipient_emails)
        rule.sender.set(sender_emails)

        data = read_settings()
        write_settings(
            {
                'rules_update': True,
                'settings_update': data.get('settings_update'),
                'save_drop': data.get('save_drop'),
                'redirect_to_sec': data.get('redirect_to_sec'),
                'sec_email': data.get('sec_email', '')
            }
        )

        return JsonResponse({
            'id': rule.id,
            'recipient': ';'.join(e.email for e in recipient_emails),
            'sender': ';'.join(e.email for e in sender_emails),
            'action': rule.action,
            'priority': rule.priority
        })

    elif request.method == 'DELETE':
        data = json.loads(request.body)
        Rule.objects.filter(id=data['id']).exclude(priority=10000).delete()
        data = read_settings()
        write_settings(
            {
                'rules_update': True,
                'settings_update': data.get('settings_update'),
                'save_drop': data.get('save_drop'),
                'redirect_to_sec': data.get('redirect_to_sec'),
                'sec_email': data.get('sec_email', '')
            }
        )
        return JsonResponse({'status': 'deleted'})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        print(data)
        write_settings({
            'rules_update': read_settings().get('rules_update'),
            'settings_update': True,
            'save_drop': data.get('save_drop') == True,
            'redirect_to_sec': data.get('redirect_to_sec') == True,
            'sec_email': data.get('sec_email', '')
        })
        return JsonResponse({'status': 'settings_saved'})


@csrf_exempt
def check_rules_update(request):
    settings = read_settings()
    if settings.get('rules_update', False) == True:
        rules = Rule.objects.all().order_by('priority')
        settings['rules_update'] = False
        write_settings(settings)
        return JsonResponse({'updated': True, 'rules': [serialize_rule(r) for r in rules]})
    else:
        return JsonResponse({'updated': False, 'status': 'ok'})

@csrf_exempt
def check_settings_update(request):
    settings = read_settings()
    if settings.get('settings_update', False) == True:
        settings['settings_update'] = False
        write_settings(settings)
        return JsonResponse({
            'updated': True,
            'settings': {
                'SAVE_DROP': settings.get('save_drop', False),
                'REDIRECT_TO_SEC': settings.get('redirect_to_sec', False),
                'SEC_EMAIL': settings.get('sec_email', '')
            }
        })
    else:
        return JsonResponse({'updated': False, 'status': 'ok'})