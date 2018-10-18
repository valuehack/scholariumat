import os
import logging
import environ
from paramiko import SSHClient
from scp import SCPClient
from tempfile import TemporaryDirectory

from django.core.files import File

from .models import FileAttachment


logger = logging.getLogger(__name__)


def download_missing_files():
    local_dir = TemporaryDirectory()
    env = environ.Env()

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect('scholarium.at', username=env('SSH_USER'), password=env('SSH_PASSWORD'))

    scp = SCPClient(ssh.get_transport())
    for attachment in FileAttachment.objects.all():
        try:
            attachment.file.open()
            attachment.file.close()
        except FileNotFoundError:
            local_path = os.path.join(local_dir.name, os.path.split(attachment.file.name)[1])

            scp.get(os.path.join('~/scholarium_daten/', attachment.file.name), local_path=local_dir.name)
            with open(local_path, 'rb') as local_file:
                attachment.file = File(local_file, name=os.path.split(attachment.file.name)[1])
                attachment.save()
            logger.debug(f'Uploaded file {attachment.file.name}')
    scp.close()
    ssh.close()


def download_old_db():
    env = environ.Env()

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect('scholarium.at', username=env('SSH_USER'), password=env('SSH_PASSWORD'))

    scp = SCPClient(ssh.get_transport())
    scp.get(os.path.join('~/scholarium_staging/db.json'))
    logger.debug(f'Downloaded db.json')

    scp.close()
    ssh.close()
