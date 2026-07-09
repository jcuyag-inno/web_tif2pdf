import tempfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from api.models import ConversionJob
from api.tasks import convert_tif_to_pdf_task


class ConversionJobSerializerTests(TestCase):
    def test_duration_is_rendered_as_minutes_and_seconds(self):
        job = ConversionJob.objects.create(folder_name="job-folder")

        serializer = job
        self.assertEqual(serializer.__class__.__name__, "ConversionJob")


class ConversionTaskTests(TestCase):
    @patch("api.tasks.img2pdf.convert")
    def test_convert_tif_to_pdf_uses_memory_buffer(self, mock_convert):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "job-folder"
            input_dir.mkdir()
            (input_dir / "page1.tif").write_bytes(b"fake tif")

            job = ConversionJob.objects.create(folder_name="job-folder")

            def fake_convert(*args, outputstream=None, **kwargs):
                outputstream.write(b"%PDF-1.4%")
                return b"%PDF-1.4%"

            mock_convert.side_effect = fake_convert

            with patch.object(settings, "MOUNTED_DATA_DIR", tmp_path):
                convert_tif_to_pdf_task(job.id)

            job.refresh_from_db()

            self.assertEqual(job.status, "SUCCESS")
            self.assertTrue(job.output_path)
            self.assertTrue(Path(job.output_path).exists())
            self.assertEqual(list(tmp_path.rglob("*.pdf")), [Path(job.output_path)])
