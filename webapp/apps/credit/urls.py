from django.urls import path

from .views import (
    ApplicationCreateView,
    ApplicationDetailView,
    ApplicationRecommendView,
    ApplicationScoreView,
    HealthView,
)

urlpatterns = [
    path('health/', HealthView.as_view()),
    path('applications/', ApplicationCreateView.as_view()),
    path('applications/<int:application_id>/', ApplicationDetailView.as_view()),
    path('applications/<int:application_id>/score', ApplicationScoreView.as_view()),
    path('applications/<int:application_id>/recommend', ApplicationRecommendView.as_view()),
]
