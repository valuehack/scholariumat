import json
import logging

from django.conf import settings

from products.models import Item, ItemType
from .models import Event, Livestream, Recording, EventType


logger = logging.getLogger(__name__)


def import_from_json():
    database = json.load(open(settings.ROOT_DIR.path('db.json')))

    # Articles
    logger.info('Importing articles...')

    events = [i for i in database if i['model'] == 'Veranstaltungen.veranstaltung']
    event_types = [i for i in database if i['model'] == 'Veranstaltungen.artderveranstaltung']

    for event in events:
        event_type = next((i for i in event_types if event['fields']['art_veranstaltung'] == i['pk']), None)

        defaults = {
            'description': event['fields']['beschreibung'],
        }

        type_name = event_type['fields']['bezeichnung']
        if type_name == 'Salon':
            type, created = EventType.objects.get_or_create(
                slug='salon', defaults={'section_title': 'Salons'})
        elif type_name == 'Seminar':
            type, created = EventType.objects.get_or_create(
                slug='seminar', defaults={'section_title': 'Seminare'})
        elif type_name == 'Vorlesung' or type_name == 'Vortrag':
            type, created = EventType.objects.get_or_create(
                slug='vortrag', defaults={'section_title': 'Vorträge'})
        else:
            raise TypeError(f'Type {type_name} not found.')
            return False

        new, created = Event.objects.update_or_create(
            title=event['fields']['bezeichnung'],
            date=event['fields']['datum'],
            type=type,
            defaults=defaults)
        if created:
            logging.debug(f'Created event {new.title}')

        if event['fields']['link']:
            livestream_type, created = ItemType.objects.get_or_create(
                slug='livestream',
                defaults={'title': 'Livestream'})

            livestream_item, created = Item.objects.get_or_create(
                product=new.product, type=livestream_type,
                defaults={'price': 5})

            livestream, created = Livestream.objects.update_or_create(
                item=livestream_item,
                defaults={'link': event['fields']['link']})
            if created:
                logging.debug(f'Created livestream for {new.title}')

        if event['fields']['datei']:
            recording_type, created = ItemType.objects.get_or_create(
                slug='recording',
                defaults={'title': 'Aufzeichnung'})

            recording_item, created = Item.objects.get_or_create(
                product=new.product, type=recording_type,
                defaults={'price': 5})

            recording, created = Recording.objects.update_or_create(
                item=recording_item,
                defaults={'file': event['fields']['datei']})
            if created:
                logging.debug(f'Created recording for {new.title}')
