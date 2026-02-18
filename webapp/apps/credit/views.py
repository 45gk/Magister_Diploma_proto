from datetime import date

from django.db import transaction
from requests import RequestException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo
from .serializers import CreditApplicationCreateSerializer, CreditApplicationDetailSerializer
from .services import call_agent_explain, call_ml_score


class ApplicationCreateView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = CreditApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_data = serializer.validated_data['client']
        app_data = serializer.validated_data['application']
        features = serializer.validated_data.get('features', {})

        client = Client.objects.create(**client_data)

        fp_data = serializer.validated_data.get('financial_profile')
        if fp_data:
            FinancialProfile.objects.create(client=client, **fp_data)

        bc_data = serializer.validated_data.get('behavioral_context')
        if bc_data:
            BehavioralContext.objects.create(client=client, **bc_data)

        app_date = app_data.get('app_date', date.today())
        application = CreditApplication.objects.create(client=client, app_date=app_date, features=features)
        return Response({"application_id": application.id}, status=status.HTTP_201_CREATED)


class ApplicationDetailView(APIView):
    def get(self, request, application_id: int):
        application = CreditApplication.objects.select_related('client').get(id=application_id)
        serializer = CreditApplicationDetailSerializer(application)
        return Response(serializer.data)


class ApplicationScoreView(APIView):
    def post(self, request, application_id: int):
        application = CreditApplication.objects.get(id=application_id)
        features = application.features or {}

        try:
            result = call_ml_score(application_id, features)
        except RequestException as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        scoring, _ = ScoringInfo.objects.update_or_create(
            application=application,
            defaults={
                'default_probability': result['default_probability'],
                'model_version': result['model_version'],
                'feature_importances': result.get('feature_importances', {}),
                'confidence': result.get('confidence', 0.0),
            },
        )
        return Response(
            {
                'application_id': application_id,
                'default_probability': scoring.default_probability,
                'model_version': scoring.model_version,
            }
        )


class ApplicationRecommendView(APIView):
    def post(self, request, application_id: int):
        application = CreditApplication.objects.get(id=application_id)
        if not hasattr(application, 'scoring'):
            return Response({"error": "scoring not found"}, status=status.HTTP_400_BAD_REQUEST)

        mode = request.data.get('mode', 'brief')
        if mode not in {'brief', 'detailed', 'policy'}:
            return Response({"error": "invalid mode"}, status=status.HTTP_400_BAD_REQUEST)

        scoring_data = {
            'default_probability': float(application.scoring.default_probability),
            'model_version': application.scoring.model_version,
            'feature_importances': application.scoring.feature_importances,
        }

        try:
            result = call_agent_explain(application_id, application.features or {}, scoring_data, mode)
        except RequestException as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        AgentExplanation.objects.update_or_create(
            application=application,
            defaults={
                'mode': mode,
                'payload': result,
            },
        )
        return Response(result)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok"})
