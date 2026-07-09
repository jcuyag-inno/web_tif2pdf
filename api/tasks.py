import img2pdf
from pathlib import Path
from celery import shared_task
from django.conf import settings
from .models import ConversionJob
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from tif2pdf.celery import app

@shared_task
def convert_tif_to_pdf_task(job_id):
    # Fetch the job record
    try:
        job = ConversionJob.objects.get(id=job_id)
    except ConversionJob.DoesNotExist:
        return

    job.status = 'PROCESSING'
    job.save()


    target_dir = settings.MOUNTED_DATA_DIR / job.folder_name

    print(target_dir)

    tif_files = sorted(
        [str(p) for p in target_dir.rglob("*") if p.suffix.lower() in ('.tif', '.tiff')]
    )

    if not tif_files:
        job.status = 'FAILED'
        job.error_message = "No TIF files found in directory."
        job.save()
        return

    job.total_files = len(tif_files)
    job.save()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    output_pdf_path = target_dir / f"{timestamp}_{job.folder_name}_converted.pdf"

    try:
        # img2pdf is efficient with RAM, but 16GB writes take time.
        # We write to a stream to keep memory usage low.
        with open(output_pdf_path, "wb") as f:
            img2pdf.convert(tif_files, outputstream=f)
            
        job.status = 'SUCCESS'
        job.processed_files = len(tif_files)
        job.output_path = str(output_pdf_path)
        job.save()

    except Exception as e:
        job.status = 'FAILED'
        job.error_message = str(e)
        job.save()
    



@app.task
def clean_orphaned_jobs():
    """
    Production Sweeper: Runs every 5-10 minutes via Celery Beat.
    Finds jobs stuck in 'PROCESSING' that haven't updated their heartbeat.
    """
    # If a 16GB file conversion takes a maximum of 20 minutes, 
    # any job unchanged for 45 minutes is a verified ghost/dead task.
    timeout_threshold = timezone.now() - timedelta(minutes=45)
    
    orphaned_jobs = ConversionJob.objects.filter(
        status='PROCESSING',
        updated_at__lt=timeout_threshold
    )
    
    for job in orphaned_jobs:
        # Option A: Mark as failed if you don't want infinite loops
        job.status = 'FAILED'
        job.error_message = "Task timed out. Worker likely suffered a hard crash or OOM."
        job.save()
        
        # Trigger external alerts here (e.g., Sentry, Slack Webhook, PagerDuty)
        # log_to_sentry(f"Job {job.id} orphaned due to worker termination.")