from django.db import models

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
