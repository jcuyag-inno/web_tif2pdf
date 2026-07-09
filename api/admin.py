from django.contrib import admin
from django.utils import timezone

from .models import ConversionJob


@admin.register(ConversionJob)
class ConversionJobAdmin(admin.ModelAdmin):
	list_display = ('id', 'folder_name', 'status', 'total_files', 'processed_files', 'duration', 'created_at', 'updated_at')
	list_filter = ('status', 'created_at', 'updated_at')
	search_fields = ('folder_name', 'error_message', 'output_path')
	readonly_fields = ('id', 'duration', 'created_at', 'updated_at')
	ordering = ('-created_at',)

	def duration(self, obj):
		if not obj.updated_at:
			return '0m 0s'
		seconds = max(0, int((timezone.now() - obj.updated_at).total_seconds()))
		minutes, secs = divmod(seconds, 60)
		return f'{minutes}m {secs}s'

	duration.short_description = 'Duration'
