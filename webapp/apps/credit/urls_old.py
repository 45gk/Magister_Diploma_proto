from django.urls import path

from .views import (
    ApplicationCreateView,
    ApplicationDetailView,
    ApplicationListView,
    ApplicationRecommendView,
    ApplicationScoreView,
    HealthView,
    IndexView,
)

app_name = 'credit'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('applications/', ApplicationListView.as_view(), name='applications-list'),
    path('applications/new/', ApplicationCreateView.as_view(), name='applications-create'),
    path('applications/<int:application_id>/', ApplicationDetailView.as_view(), name='applications-detail'),
    path('applications/<int:application_id>/score', ApplicationScoreView.as_view(), name='applications-score'),
    path('applications/<int:application_id>/recommend', ApplicationRecommendView.as_view(), name='applications-recommend'),
    path('health/', HealthView.as_view(), name='health'),
]
