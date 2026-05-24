from django.test import TestCase, Client
from django.urls import reverse
from .models import SystemSetting, Organization

class AISettingsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_seeds_ai_settings(self):
        # Verify no SystemSetting initially
        self.assertFalse(SystemSetting.objects.filter(key="AI_TONE").exists())

        # Load dashboard, which should trigger seed_data_if_empty()
        response = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Verify default AI settings were successfully seeded
        self.assertTrue(SystemSetting.objects.filter(key="AI_TONE").exists())
        self.assertEqual(SystemSetting.objects.get(key="AI_TONE").value, "EMPATHETIC")
        self.assertEqual(SystemSetting.objects.get(key="AI_LANGUAGE").value, "DE_DU")

    def test_save_ai_settings(self):
        # Seed settings first by hitting dashboard
        self.client.get(reverse('ats:dashboard'))

        # Prepare new AI settings payload
        payload = {
            'AI_TONE': 'CASUAL',
            'AI_LANGUAGE': 'DE_SIE',
            'AI_AUTO_REJECT_ENABLED': 'on',
            'AI_THRESHOLD_D_REJECT': '20',
            'AI_THRESHOLD_C_WAITLIST': '45',
            'AI_THRESHOLD_A_INVITE': '85',
            'AI_CV_LEARNING_MODE': 'true',
            'AI_AGG_CHECK_ENABLED': 'on',
            'AI_AGG_PROMPT': 'Custom AGG prompt text',
            'AI_TRANSLATE_EASY_LANGUAGE': 'true',
            'AI_EASY_LANGUAGE_PROMPT': 'Custom Easy Language prompt text',
        }

        # Save AI settings
        response = self.client.post(reverse('ats:save_ai_settings'), data=payload)
        
        # Verify redirect
        self.assertEqual(response.status_code, 302)

        # Verify values updated in DB
        self.assertEqual(SystemSetting.objects.get(key="AI_TONE").value, "CASUAL")
        self.assertEqual(SystemSetting.objects.get(key="AI_LANGUAGE").value, "DE_SIE")
        self.assertEqual(SystemSetting.objects.get(key="AI_AUTO_REJECT_ENABLED").value, "true")
        self.assertEqual(SystemSetting.objects.get(key="AI_THRESHOLD_D_REJECT").value, "20")
        self.assertEqual(SystemSetting.objects.get(key="AI_THRESHOLD_C_WAITLIST").value, "45")
        self.assertEqual(SystemSetting.objects.get(key="AI_THRESHOLD_A_INVITE").value, "85")
        self.assertEqual(SystemSetting.objects.get(key="AI_AGG_PROMPT").value, "Custom AGG prompt text")

