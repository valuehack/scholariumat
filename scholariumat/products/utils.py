import os
import logging
import environ
import json
from paramiko import SSHClient
from scp import SCPClient
from tempfile import TemporaryDirectory
from datetime import date

from django.core.files import File
from django.conf import settings

from .models import FileAttachment, Purchase, Item
from users.models import Profile
from events.models import Event


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


def import_from_json():
    database = json.load(open(settings.ROOT_DIR.path('db.json')))

    # Articles
    logger.info('Importing purchases...')

    purchases = [i for i in database if i['model'] == 'Produkte.kauf']

    for purchase in purchases:
        profile = Profile.objects.get(old_pk=purchase['fields']['nutzer'])
        model_name, obj_pk, item = str(purchase['fields']['produkt_pk']).split('+')
        if model_name == 'veranstaltung':
            try:
                event = Event.objects.get(old_pk=obj_pk)
            except Event.ObjectNotFound:
                logger.error(f'Event with pk {obj_pk} not found')

            if item == 'aufzeichnung':
                type_slug = 'recording'
            elif item == 'teilnahme':
                type_slug = 'attendance'

                try:
                    Purchase.objects.update_or_create(
                        amount=purchase['fields']['menge'],
                        profile=profile,
                        item=event.product.item_set.get(type__slug=type_slug),
                        date=date.fromisoformat(purchase['fields']['zeit'][:10]),
                        executed=True
                    )
                    logger.debug('done')
                except Item.DoesNotExist:
                    logger.error(f'Event {event} misses type {type_slug}.')
            else:
                print(item)
            
        # else:
        #     logger.error(f"Could not import {purchase['fields']['produkt_pk']}")

    logger.info('Finished importing purchases')
