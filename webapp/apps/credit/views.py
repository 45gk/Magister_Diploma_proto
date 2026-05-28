from datetime import date

from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from requests import RequestException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo
from .serializers import CreditApplicationCreateSerializer, CreditApplicationDetailSerializer
from .services import call_agent_explain, call_ml_score


class IndexView(APIView):
    def get(self, request):
        total_applications = CreditApplication.objects.count()
        total_clients = Client.objects.count()
        scored_applications = ScoringInfo.objects.count()
        recent_applications = CreditApplication.objects.order_by('-app_date')[:5]
        
        context = {
            'total_applications': total_applications,
            'total_clients': total_clients,
            'scored_applications': scored_applications,
            'recent_applications': recent_applications,
        }
        return render(request, 'credit/index.html', context)


class ApplicationListView(APIView):
    def get(self, request):
        applications = CreditApplication.objects.select_related('client', 'scoring').order_by('-app_date')
        context = {'applications': applications}
        return render(request, 'credit/applications_list.html', context)


class ApplicationCreateView(APIView):
    def get(self, request):
        return render(request, 'credit/application_create.html')
    
    @transaction.atomic
    def post(self, request):
        try:
            # Extract client data from form
            client_data = {
                'education': request.POST.get('education', ''),
                'sex': request.POST.get('sex', ''),
                'age': int(request.POST.get('age', 0)) if request.POST.get('age') else None,
                'income': request.POST.get('income') and float(request.POST.get('income')) or None,
                'car': request.POST.get('car') == 'True',
                'car_type': request.POST.get('car_type') == 'True',
                'foreign_passport': request.POST.get('foreign_passport') == 'True',
            }
            
            client = Client.objects.create(**client_data)
            
            # Financial profile
            fp_data = {
                'decline_app_cnt': int(request.POST.get('decline_app_cnt', 0)),
                'good_work': request.POST.get('good_work') == 'True',
                'bki_request_cnt': int(request.POST.get('bki_request_cnt', 0)),
                'region_rating': request.POST.get('region_rating') and float(request.POST.get('region_rating')) or None,
            }
            FinancialProfile.objects.create(client=client, **fp_data)
            
            # Behavioral context
            bc_data = {
                'home_address': request.POST.get('home_address', ''),
                'work_address': request.POST.get('work_address', ''),
                'sna': request.POST.get('sna', ''),
                'first_time': request.POST.get('first_time') == 'True',
            }
            BehavioralContext.objects.create(client=client, **bc_data)
            
            # Application
            application = CreditApplication.objects.create(client=client, app_date=date.today())
            
            messages.success(request, 'Заявка успешно создана!')
            return redirect('credit:applications-detail', application_id=application.id)
        
        except Exception as e:
            messages.error(request, f'Ошибка при создании заявки: {str(e)}')
            return render(request, 'credit/application_create.html')


class ApplicationDetailView(APIView):
    def get(self, request, application_id: int):
        application = get_object_or_404(CreditApplication.objects.select_related('client', 'scoring'), id=application_id)
        context = {'application': application}
        return render(request, 'credit/application_detail.html', context)


class ApplicationScoreView(APIView):
    def post(self, request, application_id: int):
        application = get_object_or_404(CreditApplication, id=application_id)
        features = application.features or {}
        
        try:
            result = call_ml_score(application_id, features)
            
            scoring, _ = ScoringInfo.objects.update_or_create(
                application=application,
                defaults={
                    'default_probability': result['default_probability'],
                    'model_version': result['model_version'],
                    'feature_importances': result.get('feature_importances', {}),
                    'confidence': result.get('confidence', 0.0),
                },
            )
            messages.success(request, 'Скоринг успешно выполнен!')
        except RequestException as exc:
            messages.error(request, f'Ошибка при скоринге: {str(exc)}')
        
        return redirect('credit:applications-detail', application_id=application_id)


class ApplicationRecommendView(APIView):
    def post(self, request, application_id: int):
        application = get_object_or_404(CreditApplication, id=application_id)
        
        try:
            if not hasattr(application, 'scoring') or not application.scoring:
                messages.error(request, 'Сначала необходимо провести скоринг')
                return redirect('credit:applications-detail', application_id=application_id)
            
            scoring_data = {
                'default_probability': float(application.scoring.default_probability),
                'model_version': application.scoring.model_version,
                'feature_importances': application.scoring.feature_importances,
            }
            
            result = call_agent_explain(application_id, application.features or {}, scoring_data, 'detailed')
            
            AgentExplanation.objects.update_or_create(
                application=application,
                defaults={
                    'mode': 'detailed',
                    'explanation': result.get('explanation', ''),
                    'payload': result,
                },
            )
            messages.success(request, 'Объяснение агента получено!')
        except RequestException as exc:
            messages.error(request, f'Ошибка при получении объяснения: {str(exc)}')
        
        return redirect('credit:applications-detail', application_id=application_id)


class HealthView(APIView):
    def get(self, request):
        # Check database connection
        try:
            CreditApplication.objects.count()
            database_ok = True
        except Exception:
            database_ok = False
        
        # Check ML service
        ml_service_ok = True
        try:
            call_ml_score(999, {})
        except Exception:
            ml_service_ok = False
        
        # Check Agent service
        agent_service_ok = True
        try:
            call_agent_explain(999, {}, {}, 'brief')
        except Exception:
            agent_service_ok = False
        
        health_data = {
            'web': True,
            'database': database_ok,
            'ml_service': ml_service_ok,
            'agent_service': agent_service_ok,
        }
        
        return render(request, 'credit/health.html', {'health': health_data})
