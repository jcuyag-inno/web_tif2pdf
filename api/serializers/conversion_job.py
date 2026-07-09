from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from api.models import ConversionJob


class ConversionJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ConversionJob
        fields = (
            'id',
            'folder_name',
            'status',
            'progress',
            'total_files',
            'processed_files',
            'output_path',
            'error_message',
            'duration',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'progress',
            'total_files',
            'processed_files',
            'output_path',
            'error_message',
            'duration',
            'created_at',
            'updated_at',
        )

    def get_progress(self, obj):
        return f"{obj.processed_files}/{obj.total_files}"

    def get_duration(self, obj):
        if not obj.updated_at:
            return "0m 0s"

        now = timezone.now()
        if isinstance(obj.updated_at, datetime):
            updated_at = obj.updated_at
        else:
            updated_at = timezone.make_aware(obj.updated_at)

        seconds = max(0, int((now - updated_at).total_seconds()))
        minutes, secs = divmod(seconds, 60)
        return f"{minutes}m {secs}s"
