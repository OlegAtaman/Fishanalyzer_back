from django.test import TestCase, Client
from django.urls import reverse
from analyzer.models import UploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Email, Rule
from .functions import write_settings, read_settings


class URLTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page_accessible(self):
        # Перевірка доступності головної сторінки
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_settings_page_accessible(self):
        # Перевірка доступності сторінки налаштувань
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_status_endpoint_invalid_id(self):
        # Перевірка реакції при запиті до неіснуючого файлу
        response = self.client.get(reverse('get_file_status', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_check_rules_update_default(self):
        # Перевірка відповіді при запиті оновлення правил
        response = self.client.get('/api/check_rules/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('updated', response.json())

    def test_check_settings_update_default(self):
        # Перевірка відповіді при запиті оновлення налаштувань
        response = self.client.get('/api/check_settings/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('updated', response.json())

    def test_upload_email_file(self):
        # Завантаження валідного .eml файлу
        eml_content = b"From: test@example.com\nTo: you@example.com\nSubject: Hello\n\nThis is a test email."
        uploaded_file = SimpleUploadedFile("test.eml", eml_content, content_type="message/rfc822")
        response = self.client.post(reverse('api_upload_email'), {'file': uploaded_file})
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json())

    def test_get_risk_score_nonexistent(self):
        # Перевірка відповіді для неіснуючого листа
        response = self.client.get(reverse('api_risk_score', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_get_risk_score_created(self):
        # Отримання оцінки ризику для існуючого листа
        test_file = UploadedFile.objects.create(file='test.eml', risk_score=2, status='done')
        response = self.client.get(reverse('api_risk_score', args=[test_file.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('risk_score', response.json())

    def test_settings_template_rendering(self):
        # Перевірка, що шаблон сторінки налаштувань містить ключову фразу
        response = self.client.get(reverse('settings'))
        self.assertContains(response, "Налаштування правил")

    def test_upload_invalid_method(self):
        # Використання GET замість POST для upload
        response = self.client.get(reverse('api_upload_email'))
        self.assertEqual(response.status_code, 405)


class AnalyzerViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page_loads(self):
        # Перевірка завантаження шаблону index
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyzer/index.html')

    def test_upload_email_invalid(self):
        # Відсутній файл у POST-запиті
        response = self.client.post(reverse('api_upload_email'), {})
        self.assertEqual(response.status_code, 400)

    def test_upload_email_valid(self):
        # Завантаження валідного email
        test_file = SimpleUploadedFile("test.eml", b"From: test@example.com\nTo: you@example.com\n\nHello.")
        response = self.client.post(reverse('api_upload_email'), {'file': test_file})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())

    def test_get_risk_score_not_found(self):
        # Перевірка статусу при неіснуючому id
        response = self.client.get(reverse('api_risk_score', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_firewall_settings_get(self):
        # Відображення правил на сторінці налаштувань
        Email.objects.create(email="a@a.com")
        rule = Rule.objects.create(action="drop", priority=123)
        rule.recipient.set(Email.objects.all())
        rule.sender.set(Email.objects.all())
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyzer/settings.html')


class SettingsFileTests(TestCase):
    def setUp(self):
        self.test_data = {
            "rules_update": True,
            "settings_update": True,
            "save_drop": True,
            "redirect_to_sec": True,
            "sec_email": "security@example.com"
        }

    def test_write_and_read_settings(self):
        # Перевірка збереження та зчитування settings.txt
        write_settings(self.test_data)
        result = read_settings()

        self.assertEqual(result["rules_update"], True)
        self.assertEqual(result["settings_update"], True)
        self.assertEqual(result["save_drop"], True)
        self.assertEqual(result["redirect_to_sec"], True)
        self.assertEqual(result["sec_email"], "security@example.com")