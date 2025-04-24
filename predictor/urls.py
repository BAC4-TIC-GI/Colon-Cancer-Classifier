from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('prediction-history/', views.PredictionHistoryView.as_view(), name='prediction_history'),
]