"""
Представления (_new): клон текущих + импорт CSV из банковских выгрузок.

Подключение в проект — через urls_new.py (не меняет существующие urls).
"""

from datetime import date

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from requests import RequestException
from rest_framework.response import Response
from rest_framework.views import APIView

from .csv_loader_new import get_default_csv_loader
from .models import (
    AgentExplanation,
    BehavioralContext,
    Client,
    CreditApplication,
    FinancialProfile,
    ScoringInfo,
)
from .serializers_new import CsvLoadResultSerializerNew
from .services_new import (
    call_agent_explain_new,
    call_ml_score_new,
    load_csv_directory_new,
    load_csv_upload_new,
    preview_csv_rows_new,
)


class IndexViewNew(APIView):
    def get(self, request):
        context = {
            'total_applications': CreditApplication.objects.count(),
            'total_clients': Client.objects.count(),
            'scored_applications': ScoringInfo.objects.count(),
            'recent_applications': CreditApplication.objects.order_by('-app_date')[:5],
        }
        return render(request, 'credit/index_new.html', context)


class ApplicationListViewNew(APIView):
    def get(self, request):
        applications = CreditApplication.objects.select_related('client', 'scoring').order_by('-app_date')
        return render(request, 'credit/applications_list_new.html', {'applications': applications})


class ApplicationCreateViewNew(APIView):
    def get(self, request):
        return render(request, 'credit/application_create_new.html')

    @transaction.atomic
    def post(self, request):
        try:
            client = Client.objects.create(
                education=request.POST.get('education', ''),
                sex=request.POST.get('sex', ''),
                age=int(request.POST.get('age', 0)) if request.POST.get('age') else None,
                income=request.POST.get('income') and float(request.POST.get('income')) or None,
                car=request.POST.get('car') == 'True',
                car_type=request.POST.get('car_type') == 'True',
                foreign_passport=request.POST.get('foreign_passport') == 'True',
            )
            FinancialProfile.objects.create(
                client=client,
                decline_app_cnt=int(request.POST.get('decline_app_cnt', 0)),
                good_work=request.POST.get('good_work') == 'True',
                bki_request_cnt=int(request.POST.get('bki_request_cnt', 0)),
                region_rating=request.POST.get('region_rating') and float(request.POST.get('region_rating')) or None,
            )
            BehavioralContext.objects.create(
                client=client,
                home_address=request.POST.get('home_address', ''),
                work_address=request.POST.get('work_address', ''),
                sna=request.POST.get('sna', ''),
                first_time=request.POST.get('first_time') == 'True',
            )
            application = CreditApplication.objects.create(client=client, app_date=date.today())
            messages.success(request, 'Заявка успешно создана!')
            return redirect('credit_new:applications-detail', application_id=application.id)
        except Exception as exc:
            messages.error(request, f'Ошибка при создании заявки: {exc}')
            return render(request, 'credit/application_create_new.html')


class ApplicationDetailViewNew(APIView):
    def get(self, request, application_id: int):
        application = get_object_or_404(
            CreditApplication.objects.select_related('client', 'scoring'),
            id=application_id,
        )
        return render(request, 'credit/application_detail_new.html', {'application': application})


class ApplicationScoreViewNew(APIView):
    def post(self, request, application_id: int):
        application = get_object_or_404(CreditApplication, id=application_id)
        try:
            result = call_ml_score_new(application_id, application.features or {})
            ScoringInfo.objects.update_or_create(
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
            messages.error(request, f'Ошибка при скоринге: {exc}')
        return redirect('credit_new:applications-detail', application_id=application_id)


class ApplicationRecommendViewNew(APIView):
    def post(self, request, application_id: int):
        application = get_object_or_404(CreditApplication, id=application_id)
        try:
            if not hasattr(application, 'scoring') or not application.scoring:
                messages.error(request, 'Сначала необходимо провести скоринг')
                return redirect('credit_new:applications-detail', application_id=application_id)
            scoring_data = {
                'default_probability': float(application.scoring.default_probability),
                'model_version': application.scoring.model_version,
                'feature_importances': application.scoring.feature_importances,
            }
            result = call_agent_explain_new(
                application_id,
                application.features or {},
                scoring_data,
                'detailed',
            )
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
            messages.error(request, f'Ошибка при получении объяснения: {exc}')
        return redirect('credit_new:applications-detail', application_id=application_id)


class HealthViewNew(APIView):
    def get(self, request):
        try:
            CreditApplication.objects.count()
            database_ok = True
        except Exception:
            database_ok = False
        try:
            call_ml_score_new(999, {})
            ml_service_ok = True
        except Exception:
            ml_service_ok = False
        try:
            call_agent_explain_new(999, {}, {}, 'brief')
            agent_service_ok = True
        except Exception:
            agent_service_ok = False
        health_data = {
            'web': True,
            'database': database_ok,
            'ml_service': ml_service_ok,
            'agent_service': agent_service_ok,
        }
        return render(request, 'credit/health_new.html', {'health': health_data})


# ---------------------------------------------------------------------------
# Импорт CSV (Home Credit / models_1)
# ---------------------------------------------------------------------------


class CsvImportIndexViewNew(APIView):
    """Список поддерживаемых выгрузок и форма загрузки."""

    def get(self, request):
        loader = get_default_csv_loader()
        datasets = loader.supported_datasets()
        return render(
            request,
            'credit/csv_import_new.html',
            {'datasets': datasets},
        )


class CsvImportUploadViewNew(APIView):
    """POST: загрузка одного CSV-файла."""

    def post(self, request):
        dataset_key = request.POST.get('dataset_key', '').strip()
        uploaded = request.FILES.get('csv_file')
        strip_junk = request.POST.get('strip_junk', 'on') == 'on'
        enrich_junk = request.POST.get('enrich_junk') == 'on'
        limit_raw = request.POST.get('limit', '').strip()
        limit = int(limit_raw) if limit_raw.isdigit() else None

        if not dataset_key or not uploaded:
            messages.error(request, 'Укажите тип выгрузки и файл CSV')
            return redirect('credit_new:csv-import')

        result = load_csv_upload_new(
            dataset_key,
            uploaded,
            strip_junk=strip_junk,
            enrich_junk=enrich_junk,
            limit=limit,
        )
        if result.ok:
            messages.success(request, f'Загружено строк: {result.row_count}')
        else:
            messages.error(request, '; '.join(result.errors) or 'Ошибка загрузки')

        context = {
            'result': result,
            'preview_rows': preview_csv_rows_new(result),
            'serialized': CsvLoadResultSerializerNew.from_load_result(result),
        }
        return render(request, 'credit/csv_import_result_new.html', context)


class CsvImportDirectoryViewNew(APIView):
    """POST: путь к каталогу с Kaggle CSV (для dev/бэкенд)."""

    def post(self, request):
        directory = request.POST.get('directory', '').strip()
        if not directory:
            messages.error(request, 'Укажите путь к каталогу')
            return redirect('credit_new:csv-import')

        batch = load_csv_directory_new(directory, limit_per_file=100)
        summaries = []
        for key, res in batch.results.items():
            summaries.append({
                'dataset': key,
                'row_count': res.row_count,
                'ok': res.ok,
                'errors': res.errors,
            })
        context = {'batch': batch, 'summaries': summaries}
        return render(request, 'credit/csv_import_batch_new.html', context)


class CsvImportApiViewNew(APIView):
    """JSON API: загрузка CSV (для интеграции без HTML)."""

    def post(self, request):
        dataset_key = request.data.get('dataset_key') or request.POST.get('dataset_key')
        uploaded = request.FILES.get('csv_file')
        if not dataset_key or not uploaded:
            return Response({'error': 'dataset_key и csv_file обязательны'}, status=400)

        result = load_csv_upload_new(
            dataset_key,
            uploaded,
            strip_junk=request.data.get('strip_junk', True),
            enrich_junk=request.data.get('enrich_junk', False),
            limit=request.data.get('limit'),
        )
        return Response(CsvLoadResultSerializerNew.from_load_result(result))
