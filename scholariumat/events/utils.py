import json
import logging
import os
import pypandoc

from django.conf import settings

from products.models import Item, ItemType, FileAttachment, AttachmentType
from .models import Event, Livestream, EventType


logger = logging.getLogger(__name__)


def import_from_json():
    database = json.load(open(settings.ROOT_DIR.path('db.json')))

    # Articles
    logger.info('Importing events...')

    events = [i for i in database if i['model'] == 'Veranstaltungen.veranstaltung']
    event_types = [i for i in database if i['model'] == 'Veranstaltungen.artderveranstaltung']

    for type in event_types:
        type_name = type['fields']['bezeichnung']
        description = pypandoc.convert(type['fields']['beschreibung'], 'md', format='html')
        if type_name == 'Salon':
            type, created = EventType.objects.update_or_create(
                slug='salon',
                defaults={'title': type_name, 'section_title': 'Salons', 'description': description})
        elif type_name == 'Seminar':
            type, created = EventType.objects.update_or_create(
                slug='seminar',
                defaults={'title': type_name, 'section_title': 'Seminare', 'description': description})
        elif type_name == 'Vorlesung' or type_name == 'Vortrag':
            type, created = EventType.objects.update_or_create(
                slug='vortrag',
                defaults={'title': 'Vortrag', 'section_title': 'Vorträge'})

    for event in events:
        event_type = next((i for i in event_types if event['fields']['art_veranstaltung'] == i['pk']), None)

        defaults = {
            'description': pypandoc.convert(event['fields']['beschreibung'], 'md', format='html')
        }

        type_name = event_type['fields']['bezeichnung']
        if type_name == 'Salon':
            type = EventType.objects.get(slug='salon',)
        elif type_name == 'Seminar':
            type = EventType.objects.get(slug='seminar')
        elif type_name == 'Vorlesung' or type_name == 'Vortrag':
            type = EventType.objects.get(slug='vortrag')

        new, created = Event.objects.update_or_create(
            title=pypandoc.convert(event['fields']['bezeichnung'], 'md', format='html'),
            date=event['fields']['datum'],
            type=type,
            defaults=defaults)
        if created:
            logging.debug(f'Created event {new.title}')

        livestream_type, created = ItemType.objects.get_or_create(
            slug='livestream',
            defaults={'title': 'Livestream'})
        recording_type, created = ItemType.objects.get_or_create(
            slug='recording',
            defaults={'title': 'Aufzeichnung'})

        livestream_item = None

        if event['fields']['link']:
            livestream_item, created = Item.objects.get_or_create(
                product=new.product, type=livestream_type,
                defaults={'price': 5})

            livestream, created = Livestream.objects.update_or_create(
                item=livestream_item,
                defaults={'link': event['fields']['link']})
            if created:
                logging.debug(f'Created livestream for {new.title}')

        if event['fields']['datei']:
            attachment_type, created = AttachmentType.objects.get_or_create(
                slug='mp3', defaults={'title': 'MP3'})

            file_name = os.path.split(event['fields']['datei'])[1]
            downloaded = FileAttachment.objects.filter(
                type=attachment_type,
                file=file_name)
            if downloaded:
                recording = downloaded.get()
            else:
                recording, created = FileAttachment.objects.get_or_create(
                    type=attachment_type,
                    file=event['fields']['datei'])

            recording_item, created = Item.objects.get_or_create(
                product=new.product, type=recording_type,
                defaults={'price': 5})

            recording_item.files.add(recording)
            if livestream_item:
                livestream_item.files.add(recording)

            if created:
                logging.debug(f'Created recording for {new.title}')
