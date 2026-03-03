from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


class CreditFlowTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()

    def test_create_application(self):
        payload = {
            "client": {
                "education": "higher",
                "sex": "F",
                "age": 30,
                "car": True,
                "car_type": False,
                "income": 100000,
                "foreign_passport": True,
            },
            "application": {"app_date": "2026-02-18"},
            "features": {"income": 100000, "debt_to_income": 0.35},
        }
        response = self.client_api.post('/applications/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('application_id', response.data)

    @patch('apps.credit.views.call_ml_score')
    def test_score_endpoint(self, ml_mock):
        create_resp = self.client_api.post(
            '/applications/',
            {
                "client": {"education": "h", "sex": "M", "age": 32, "car": False, "car_type": False, "income": 80000, "foreign_passport": False},
                "application": {"app_date": "2026-02-18"},
                "features": {"income": 80000, "debt_to_income": 0.4},
            },
            format='json',
        )
        app_id = create_resp.data['application_id']
        ml_mock.return_value = {
            "default_probability": 0.42,
            "model_version": "v1.0",
            "feature_importances": {"income": -0.12},
            "confidence": 0.88,
        }
        response = self.client_api.post(f'/applications/{app_id}/score', {}, format='json')
        self.assertEqual(response.status_code, 200)

    @patch('apps.credit.views.call_agent_explain')
    @patch('apps.credit.views.call_ml_score')
    def test_recommend_endpoint(self, ml_mock, agent_mock):
        create_resp = self.client_api.post(
            '/applications/',
            {
                "client": {"education": "h", "sex": "M", "age": 32, "car": False, "car_type": False, "income": 80000, "foreign_passport": False},
                "application": {"app_date": "2026-02-18"},
                "features": {"income": 80000, "debt_to_income": 0.4},
            },
            format='json',
        )
        app_id = create_resp.data['application_id']
        ml_mock.return_value = {
            "default_probability": 0.42,
            "model_version": "v1.0",
            "feature_importances": {"income": -0.12},
            "confidence": 0.88,
        }
        self.client_api.post(f'/applications/{app_id}/score', {}, format='json')
        agent_mock.return_value = {"application_id": app_id, "recommendations": []}
        response = self.client_api.post(f'/applications/{app_id}/recommend', {"mode": "brief"}, format='json')
        self.assertEqual(response.status_code, 200)
