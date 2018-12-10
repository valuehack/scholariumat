import logging
from pyzotero import zotero, zotero_errors
from slugify import slugify
from dateutil.parser import parse
from weasyprint import HTML
import re

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import mail_managers
from django.urls import reverse_lazy

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.models import Purchase, ItemType, AttachmentType
from products.behaviours import AttachmentBase, ProductBase
from framework.behaviours import CommentAble, PermalinkAble


logger = logging.getLogger(__name__)


class ZotAttachment(AttachmentBase):

    FORMAT_CHOICES = [
        ('file', 'Datei'),
        ('note', 'Notiz')
    ]

    key = models.CharField(max_length=100, blank=True)
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES)

    def get(self):
        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        if self.format == 'note':

            html = zot.item(self.key)['data']['note']
            path = f'{settings.TMP_DIR}/{self.key}.pdf'
            HTML(string=html).write_pdf(path)

            logger.debug(f'Conversion to pdf successfull: {self.key}')
            with open(path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=f'application/pdf')
        elif self.format == 'file':
            try:
                file = zot.file(self.key)
            except zotero_errors.ResourceNotFound:
                logger.exception(f'Zotero: File at {self.key} is missing!')
                return False
            response = HttpResponse(file, content_type=f'application/{self.type.slug}')

        response['Content-Disposition'] = f'attachment; \
            filename={slugify(self.item.product.zotitem.title)}.pdf'
        return response


class Collection(TitleSlugDescriptionModel, PermalinkAble):
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    @property
    def children(self):
        return self.__class__.objects.filter(parent=self)

    @property
    def num_items(self):
        items = 0
        for child in self.children:
            items += child.num_items
        items += len(ZotItem.objects.filter(collection=self))
        return items

    def sync(self):
        """
        Retrieves and saves metadata from all items, attachments and notes inside the collection from zotero.
        """
        logger.info('Retrieving items in {}'.format(self.title))

        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        items = zot.everything(zot.collection_items(self.slug))

        # Seperate items and attachments/notes
        parents, children = [], []
        for item in items:
            if 'parentItem' in item['data']:
                children.append(item)
            elif item['data']['itemType'] in settings.ZOTERO_ITEM_TYPES:
                parents.append(item)

        logger.info('updating items...')

        for item in parents:
            zot_item = ZotItem.update_or_create_from_data(item['key'], item['data'])
            zot_item.collection.add(self)

        # Remove failed authors
        Author.remove_failed_authors()

        # Remove deleted zotero items
        logger.info('cleaning up...')
        parent_keys = [parent['data']['key'] for parent in parents]
        for zot_item in ZotItem.objects.filter(collection=self):
            if zot_item.slug not in parent_keys:
                zot_item.delete()

        logger.info('updating attachments/notes...')

        for child in children:
            type_defaults = {
                'shipping': False,
                'buy_once': True,
                'accessible_at': 300,
                'purchasable_at': 300,
                'default_price': settings.DEFAULT_FILE_PRICE
            }

            try:
                zot_item = ZotItem.objects.get(slug=child['data']['parentItem'])
            except ObjectDoesNotExist:
                continue

            if child['data']['itemType'] == 'attachment' and 'filename' in child['data']:
                type = child['data']['filename'].split('.')[-1]  # Get file type

                if type in settings.DOWNLOAD_FORMATS:
                    type_defaults['title'] = type.upper()
                else:
                    continue

                if zot_item.scholarium:
                    type_defaults['accessible_at'] = None
                    type_defaults['purchasable_at'] = 0
                    type = f'scholarium_{type}'

            elif child['data']['itemType'] == 'note':
                type = 'note'
                type_defaults['title'] = 'Exzerpt'
            else:
                continue

            # Create purchasable Item
            zot_item.update_or_create_item(
                type=type,
                type_defaults=type_defaults,
                file_key=child['data']['key'])

        # Remove deleted attachments/notes
        logger.info('cleaning up...')
        child_keys = [child['data']['key'] for child in children]
        for zot_item in ZotItem.objects.filter(collection=self):
            for item in zot_item.product.item_set.filter(type__slug__in=settings.DOWNLOAD_FORMATS):
                attachments = ZotAttachment.objects.filter(item=item)
                for attachment in attachments:
                    if attachment.key not in child_keys:
                        attachment.delete()
                if not item.attachments:
                    item.delete()

        logger.info('Sync finished.')

    def get_parents(self):
        parents = []
        parent = self.parent
        while(parent):
            parents.append(parent)
            parent = parent.parent
        return parents

    def __str__(self):
        return self.title

    @classmethod
    def retrieve(cls):
        """
        Retrieve all non-hidden remote collections from Zotero.
        """
        logger.info('retrieving collections...')
        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        collections = [collection for collection in zot.collections() if collection['data']['name'][0] != '_']

        def save_collections(parent_key, collections):
            """
            Saves parent and childcollections recursively as models.
            """
            for collection in [c for c in collections if c['data']['parentCollection'] == parent_key]:
                key = collection['data']['key']
                name = collection['data']['name']
                parent = cls.objects.get(slug=parent_key) if parent_key else None
                local_collection, created = cls.objects.update_or_create(
                    slug=key,
                    defaults={'title': name, 'parent': parent})
                logger.debug('Collection {} saved.'.format(name))

                save_collections(key, collections)

        # Check for collections to delete
        logger.debug('cleaning up...')
        collection_keys = [collection['data']['key'] for collection in collections]
        for local_collection in cls.objects.all():
            if local_collection.slug not in collection_keys:
                edit_url = reverse_lazy('admin:library_collection_change', args=[local_collection.pk])
                mail_managers(
                    f'Kollektion zu löschen: {local_collection.title}',
                    f'Die Kollektion {local_collection.title} scheint in Zotero nicht mehr zu existieren. '
                    f'Falls dies richtig ist, bitte per Hand löschen: {settings.DEFAULT_DOMAIN}{edit_url}.')
                logger.debug('Collection {} marked for deletion.'.format(local_collection.title))

        save_collections(False, collections)

    class Meta:
        verbose_name = 'Kollektion'
        verbose_name_plural = 'Kollektionen'


class Author(models.Model):
    name = models.CharField(max_length=255)

    @classmethod
    def remove_failed_authors(cls):
        for author in cls.objects.filter(zotitem__isnull=True):
            logger.debug('Deleted author {}'.format(author.name))
            author.delete()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autoren'


class ZotItem(ProductBase):
    title = models.CharField(max_length=1000)  # Can be very long.
    slug = models.CharField(max_length=50, unique=True)
    authors = models.ManyToManyField(Author)
    published = models.DateField(blank=True, null=True)
    collection = models.ManyToManyField(Collection)
    scholarium = models.BooleanField(default=False)  # If item is physically present in library
    amount = models.SmallIntegerField(null=True, blank=True)

    @property
    def lendings_active(self):
        return self.lending_set.filter(returned__isnull=True)

    @property
    def lendings_possible(self):
        try:
            return self.product.item_set.get(type__title='Leihe').amount - len(self.lendings_active)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def update_or_create_from_data(cls, key, data):
        """
        Given API data from Zotero as dict, update or create a ZotItem.
        """
        item_data = {}

        # Get title
        try:
            title = data.get('title') or data['subject']  # Sometimes title is missing
        except KeyError as e:
            logger.exception(e)
            return None

        # Get date
        date = data.get('date')
        try:
            date = parse(date) if date else None
        except ValueError:
            logger.debug(f'Date {date} not recognized: {title}. skipping.')

        # Get extra variables
        # TODO: get price, additional_supply from variables
        extra_variables = dict(re.findall(r'{(\w+):\s(\w+)}', data.get('extra', '')))

        # Get amount
        amount = extra_variables.get('amount')
        if not amount:
            tags = [tag['tag'] for tag in data['tags']]
            if any([tag in tags for tag in settings.ZOTERO_PUBLISHER_TAGS]):
                amount = 1

        # Get/Set authors
        authors = []
        for creator in data.get('creators', []):
            names = list(filter(None, [creator.get(name_key) for name_key in ['firstName', 'name', 'lastName']]))
            full_name = ' '.join(names)
            author, created = Author.objects.get_or_create(name=full_name)
            authors.append(author)

        item_data = {
            'title': title,
            'published': date,
            'amount': amount
        }

        zot_item, created = cls.objects.update_or_create(slug=key, defaults=item_data)
        zot_item.authors.clear()
        zot_item.authors.add(*authors)

        logger.debug(f'Saved item {zot_item.title}. Created: {created}')

    def update_or_create_purchase_item(self, price=None, printing=False):
        """
        Updates purchasable items for a Zotero Item
        """
        itemtype = ItemType.objects.filter(slug__contains='purchase').update_or_create(
            default_amount=1,
            shipping=True,
            request_price=True,
            additional_supply=printing,
            defaults={
                'slug': f'{self.collection.title}_purchase'
            })
        self.product.item_set.update_or_create(
            type=itemtype,
            defaults={
                'amount': self.amount,
                'price': price,
            })

    def update_or_create_item(self, type, type_defaults={}, item_defaults={}, file_key=None):
        """
        Creates/Updates a purchasable item from format/type string. Creates ItemType and Attachment as needed.
        """
        # Create item type if not present
        itemtype, created = ItemType.objects.get_or_create(slug=type, defaults=type_defaults)
        if created:
            logger.debug('Created item type {}'.format(itemtype))

        item = self.product.item_set.update_or_create(type=itemtype, defaults=item_defaults)[0]

        if file_key:  # Create/Update attachment if necessary
            attachment_type, created = AttachmentType.objects.get_or_create(slug='pdf', defaults={'title': 'PDF'})
            if created:
                logger.debug('Created attachment type {}'.format(attachment_type))
            defaults = {
                'key': file_key,
                'type': attachment_type
            }
            if type == 'note':
                defaults['format'] = type
            else:
                defaults['format'] = 'file'
            attachment, created = ZotAttachment.objects.update_or_create(item=item, defaults=defaults)
        return item

    def __str__(self):
        return '%s (%s)' % (self.title, ', '.join([author.__str__() for author in self.authors.all()]))

    class Meta:
        verbose_name = 'Zotero Item'
        verbose_name_plural = 'Zotero Items'


class Lending(TimeStampedModel, CommentAble):
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE)
    returned = models.DateField(blank=True, null=True)
    charged = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = 'Leihe'
        verbose_name_plural = 'Leihen'
