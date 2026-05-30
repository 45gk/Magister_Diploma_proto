"""
URL-маршруты (_new). Подключите в credit_system/urls.py, например:

    path('new/', include('apps.credit.urls_new')),
"""

from django.urls import path

from .views_new import (
    ApplicationCreateViewNew,
    ApplicationDetailViewNew,
    ApplicationListViewNew,
    ApplicationRecommendViewNew,
    ApplicationScoreViewNew,
    CsvImportApiViewNew,
    CsvImportDirectoryViewNew,
    CsvImportIndexViewNew,
    CsvImportUploadViewNew,
    HealthViewNew,
    IndexViewNew,
)

# from .views import *

app_name = 'credit_new'

urlpatterns = [
    path('', IndexViewNew.as_view(), name='index'),
    path('applications/', ApplicationListViewNew.as_view(), name='applications-list'),
    path('applications/new/', ApplicationCreateViewNew.as_view(), name='applications-create'),
    path('applications/<int:application_id>/', ApplicationDetailViewNew.as_view(), name='applications-detail'),
    path('applications/<int:application_id>/score', ApplicationScoreViewNew.as_view(), name='applications-score'),
    path(
        'applications/<int:application_id>/recommend',
        ApplicationRecommendViewNew.as_view(),
        name='applications-recommend',
    ),
    path('health/', HealthViewNew.as_view(), name='health'),
    # CSV import
    path('import/csv/', CsvImportIndexViewNew.as_view(), name='csv-import'),
    path('import/csv/upload/', CsvImportUploadViewNew.as_view(), name='csv-upload'),
    path('import/csv/directory/', CsvImportDirectoryViewNew.as_view(), name='csv-directory'),
    path('api/import/csv/', CsvImportApiViewNew.as_view(), name='csv-api'),
]
