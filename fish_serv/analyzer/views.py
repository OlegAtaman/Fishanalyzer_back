from django.shortcuts import render, redirect
from .models import UploadedFile
from django.http import JsonResponse
from .parser import parse_eml
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UploadedFileSerializer



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
    
def firewall_settings(request):
    return render(request, 'analyzer/settings.html')