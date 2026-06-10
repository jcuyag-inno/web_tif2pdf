from django.urls import path
from .views import ConversionJobListCreateView, ConversionJobRetrieveView

app_name = 'api'

urlpatterns = [
    path('jobs/', ConversionJobListCreateView.as_view(), name='job_list_create'),
    path('jobs/<uuid:job_id>/', ConversionJobRetrieveView.as_view(), name='job_detail'),
]
