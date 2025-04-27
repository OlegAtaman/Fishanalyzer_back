from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class UploadedFile(models.Model):
    STATUS_CHOICES = [
        ('analyzing', 'Аналізується'),
        ('done', 'Завершено'),
        ('error', 'Помилка'),
    ]

    file = models.FileField(upload_to='')
    risk_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='done')

    def __str__(self):
        return f"{self.file.name} (Risk: {self.risk_score})"


class Link(models.Model):
    STATUS_CHOICES = [
        ('analyzing', 'Аналізується'),
        ('done', 'Завершено'),
        ('error', 'Помилка'),
    ]

    email = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='links')
    url = models.URLField()
    risk_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='done')

    def __str__(self):
        return f"{self.url} (Risk: {self.risk_score})"


class Attachment(models.Model):
    STATUS_CHOICES = [
        ('analyzing', 'Аналізується'),
        ('done', 'Завершено'),
        ('error', 'Помилка'),
    ]

    email = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    risk_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='done')

    def __str__(self):
        return f"{self.filename} (Risk: {self.risk_score})"


class Email(models.Model):
    email = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.email


class Rule(models.Model):
    ACTION_CHOICES = [
        ('allow', 'Дозволити'),
        ('check', 'Перевіряти'),
        ('drop', 'Заборонити'),
    ]

    sender = models.ManyToManyField(Email, related_name='sender_rules')
    recipient = models.ManyToManyField(Email, related_name='recipient_rules')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='drop')
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000)])

    class Meta:
        ordering = ['priority']

    def __str__(self):
        return f"#{self.id}: {self.action.upper()} (P{self.priority})"