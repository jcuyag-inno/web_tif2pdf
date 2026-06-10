import uuid
from django.db import models

class ConversionJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Progress tracking
    total_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    
    # Metadata and Logs
    output_path = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "PDF conversion job"
        verbose_name_plural = "PDF conversion jobs"

    def __str__(self):
        return f"{self.folder_name} - {self.status}"
