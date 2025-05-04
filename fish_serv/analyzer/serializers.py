from rest_framework import serializers
from .models import UploadedFile

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'status', 'risk_score']
        read_only_fields = ['id', 'status', 'risk_score']


def serialize_rule(rule):
    return {
        'id': rule.id,
        'recipient': [email.email for email in rule.recipient.all()],
        'sender': [email.email for email in rule.sender.all()],
        'action': rule.action,
        'priority': rule.priority,
    }