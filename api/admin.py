from django.contrib import admin
from .models import ConversionJob


@admin.register(ConversionJob)
class ConversionJobAdmin(admin.ModelAdmin):
	list_display = ('id', 'folder_name', 'status', 'total_files', 'processed_files', 'created_at', 'updated_at')
	list_filter = ('status', 'created_at', 'updated_at')
	search_fields = ('folder_name', 'error_message', 'output_path')
	readonly_fields = ('id', 'created_at', 'updated_at')
	ordering = ('-created_at',)
