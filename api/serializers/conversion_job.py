from rest_framework import serializers

from api.models import ConversionJob


class ConversionJobSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

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
            'created_at',
            'updated_at',
        )

    def get_progress(self, obj):
        return f"{obj.processed_files}/{obj.total_files}"
