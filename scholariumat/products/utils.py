import os
import logging
import environ
import json
import html
from paramiko import SSHClient
from paramiko.client import AutoAddPolicy
from scp import SCPClient, SCPException
from tempfile import TemporaryDirectory
from datetime import date

from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from .models import FileAttachment, Purchase, Item
from users.models import Profile
from events.models import Event
from library.models import ZotItem


logger = logging.getLogger(__name__)


def download_missing_files():
    local_dir = TemporaryDirectory()
    env = environ.Env()

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.connect('scholarium.at', username=env('SSH_USER'), password=env('SSH_PASSWORD'))

    scp = SCPClient(ssh.get_transport())
    for attachment in FileAttachment.objects.all():
        try:
            attachment.file.open()
            attachment.file.close()
        except (FileNotFoundError, OSError):
            local_path = os.path.join(local_dir.name, os.path.split(attachment.file.name)[1])

            try:
                scp.get(os.path.join('~/scholarium_daten/', attachment.file.name), local_path=local_dir.name)
            except SCPException:
                # File doesn't exist, delete item, attachment
                logger.error(f'Could not find file {attachment.file.name}. Deleting attachment.')
                for item in attachment.item_set.all():
                    if len(item.files.all()) == 1:
                        logger.info(f'Deleted item {item}, as attachment is missing.')
                        item.delete()
                attachment.delete()
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
    ssh.set_missing_host_key_policy(AutoAddPolicy)
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
    books = {b['pk']: b for b in database if b['model'] == 'Scholien.buechlein'}

    scholien_ids = {
        "256": "MCR3ZQU3",
        "257": "USD2L6KA",
        "258": "8NBLK5G8",
        "259": "WXDF6D3G",
        "260": "CESGVT8M",
        "261": "2N3SEHPE",
        "262": "GJ5EIUBE",
        "263": "IPWGSJFZ",
        "264": "NQTPG7DC",
        "265": "H4LFJT2E",
        "266": "BSEL4CAC",
        "267": "C5887VAP",
        "268": "WBT88SYW",
        "269": "HST3NRRM",
        "270": "N462K266",
        "271": "4SJATDE8",
        "272": "YQLB4G6A",
        "273": "L8WQWXFY",
        "274": "WQVN6XVK",
        "275": "LWQVYW4W",
        "276": "P5EVRZIP",
        "277": "P9W42ZH4",
        "278": "MVP4B5N9",
        "279": "RG6S5Q4S",
        "280": "V4GSELBB",
        "281": "TIL9PMDX",
        "282": "YEDIDSES",
        "283": "2E6UXPDE",
        "284": "JXSBIBMG",
        "285": "Q55ZFFFP",
        "286": "8SLANL6H",
        "287": "NHLDRB6E",
        "288": "XYVJA64Q",
        "253": "PDMBTCI5",
        "254": "BASKFMJG",
        "255": "U96XFM9H"
    }

    for purchase in purchases:

        if purchase['fields']['nutzer'] is None:
            continue

        try:
            profile = Profile.objects.get(old_pk=purchase['fields']['nutzer'])
        except MultipleObjectsReturned:
            logger.error('Multiple profiles returned:')
            logger.error(Profile.objects.filter(old_pk=purchase['fields']['nutzer']))
            continue
        model_name, obj_pk, item = str(purchase['fields']['produkt_pk']).split('+')
        if model_name == 'veranstaltung':
            try:
                event = Event.objects.get(old_pk=obj_pk)
            except ObjectDoesNotExist:
                logger.error(f'Event with pk {obj_pk} not found')
                continue

            if item == 'aufzeichnung':
                type_slug = 'recording'
            elif item == 'teilnahme':
                type_slug = 'attendance'
            elif item == 'livestream':
                type_slug = 'livestream'
            else:
                logger.error(item)

            try:
                local_purchase, created = Purchase.objects.update_or_create(
                    amount=purchase['fields']['menge'],
                    profile=profile,
                    item=event.product.item_set.get(type__slug__contains=type_slug),
                    date=date(*map(int, purchase['fields']['zeit'][:10].split('-'))),
                    executed=True
                )
                if created:
                    local_purchase.item.sell(local_purchase.amount)
                logger.debug(f'{local_purchase.item} purchase successfully imported')
            except Item.DoesNotExist:
                logger.error(f'Event {event} misses type {type_slug}.')
        elif model_name == 'buechlein':
            book = books[int(obj_pk)]
            title = html.unescape(book['fields']['bezeichnung'].split(' ')[-1])
            zotero_id = scholien_ids[obj_pk]
            try:
                zotitem = ZotItem.objects.get(slug=zotero_id)
            except ObjectDoesNotExist:
                logger.error(f'No object found for {title} with id {zotero_id}, pk {obj_pk}')
                continue

            if item in ['pdf', 'epub', 'mobi']:
                try:
                    Purchase.objects.update_or_create(
                        amount=1,
                        profile=profile,
                        item=zotitem.product.item_set.get(type__slug__contains='pdf'),
                        date=date(*map(int, purchase['fields']['zeit'][:10].split('-'))),
                        executed=True
                    )
                    logger.debug(f'Zotitem purchase for {title} successfully imported')
                except ObjectDoesNotExist:
                    logger.error(f'Item {title} as {item} not found')
        elif model_name not in ['buch', 'studiumdings']:
            logger.error(f"Could not import {purchase['fields']['produkt_pk']}")

    logger.info('Finished importing purchases')
