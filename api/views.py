from rest_framework import generics, status
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import ConversionJob
from .serializers import ConversionJobSerializer
from .tasks import convert_tif_to_pdf_task


class ConversionJobFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=ConversionJob.STATUS_CHOICES)

    class Meta:
        model = ConversionJob
        fields = ('status',)


class ConversionJobListCreateView(generics.ListCreateAPIView):
    queryset = ConversionJob.objects.all().order_by('-created_at')
    serializer_class = ConversionJobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConversionJobFilter

    def perform_create(self, serializer):
        job = serializer.save()
        convert_tif_to_pdf_task.delay(str(job.id))

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.status_code = status.HTTP_202_ACCEPTED
        return response


class ConversionJobRetrieveView(generics.RetrieveAPIView):
    queryset = ConversionJob.objects.all()
    serializer_class = ConversionJobSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'job_id'