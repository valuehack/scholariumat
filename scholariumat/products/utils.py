import os
import logging
from tempfile import TemporaryDirectory

from django.core.files import File
from django.conf import settings

from .models import FileAttachment


logger = logging.getLogger(__name__)


def upload_files():

    imported_media_path = os.path.join(settings.ROOT_DIR, 'scholarium_daten/')

    for attachment in FileAttachment.objects.all():
        try:
            attachment.file.open()
            attachment.file.close()
        except FileNotFoundError:
            try:
                with open(os.path.join(imported_media_path, attachment.file.name)) as local_file:
                    # TODO: Use temporary directory
                    attachment.file = File(local_file)
                    attachment.save()
                logger.debug(f'Uploaded file {attachment.file.name}')
            except FileNotFoundError:
                logger.error(f'No local file found for {attachment.file.name}')
