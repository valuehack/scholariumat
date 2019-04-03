import logging
from pyzotero import zotero, zotero_errors
from slugify import slugify
from dateutil.parser import parse
from weasyprint import HTML
from pyzotero.zotero_errors import ResourceNotFound
import re

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import mail_admins

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.models import Purchase, ItemType, AttachmentType, Item
from products.behaviours import AttachmentBase, ProductBase
from framework.behaviours import CommentAble, PermalinkAble


logger = logging.getLogger(__name__)


def handle_protected(error):
    logger.error(f'Failed to delete item: {error}')
    mail_admins(f'Can not delete protected item', f"{error}")


class ZotAttachment(AttachmentBase):

    FORMAT_CHOICES = [
        ('file', 'Datei'),
        ('note', 'Exzerpt')
    ]

    key = models.CharField(max_length=100, blank=True)
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES)
    zotitem = models.ForeignKey('ZotItem', on_delete=models.CASCADE, null=True, blank=True)

    ITEMTYPE_DEFAULTS = {
        'shipping': False,
        'request_price': True,
        'additional_supply': False,
        'default_price': 5,
        'default_amount': None,
        'purchasable_at': 300,
        'accessible_at': 300,
        'buy_once': True,
        'expires_on_product_date': False,
        'buy_unauthenticated': False,
        'inform_staff': False,
    }

    @classmethod
    def update_or_create_from_data(cls, data):
        if data['itemType'] == 'attachment' and 'filename' in data:
            format = 'file'
            type = data['filename'].split('.')[-1]
            if type not in settings.DOWNLOAD_FORMATS:
                return None
        elif data['itemType'] == 'note' and data['note'].startswith('<p><strong>Yellow Annotations'):
            format = 'note'
            type = 'pdf'
        else:
            return None

        try:
            zotitem = ZotItem.objects.get(slug=data['parentItem'])
        except ZotItem.DoesNotExist:
            return None

        attachment_type, created = AttachmentType.objects.get_or_create(slug=type, defaults={'title': type.upper()})
        attachment, created = cls.objects.update_or_create(
            key=data['key'], defaults={'format': format, 'zotitem': zotitem, 'type': attachment_type})
        attachment.update_or_create_item()

        return attachment

    def update_or_create_item(self):
        if self.type.slug not in settings.DOWNLOAD_FORMATS:
            if self.item:
                try:
                    self.item.delete()
                except models.ProtectedError as e:
                    handle_protected(e)
            return None

        if self.format == 'note':
            slug = 'note'
            title = 'Exzerpt'
        else:
            slug = self.type.slug
            title = self.type.title

        type_defaults = self.ITEMTYPE_DEFAULTS
        type_defaults['title'] = title

        price = self.zotitem.price_digital or self.ITEMTYPE_DEFAULTS['default_price']
        item_defaults = {'_price': price}

        item_type, created = ItemType.objects.update_or_create(slug=slug, defaults=type_defaults)
        item_defaults['type'] = item_type

        item, created = self.zotitem.product.item_set.update_or_create(zotattachment=self, defaults=item_defaults)
        self.item = item
        self.save()

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
        try:
            items = zot.everything(zot.collection_items(self.slug))
        except ResourceNotFound:
            logger.warning(f'Revoming collection {self.title}')
            self.delete()
            return None

        # Seperate items and attachments/notes
        parents, children = [], []
        for item in items:
            if 'parentItem' in item['data']:
                children.append(item)
            elif item['data']['itemType'] in settings.ZOTERO_ITEM_TYPES:
                parents.append(item)

        logger.info('updating items...')

        for item in parents:
            zotitem = ZotItem.update_or_create_from_data(item['data'])
            if zotitem:
                zotitem.collection.add(self)

        logger.info('cleaning up...')

        # Remove failed authors
        Author.objects.filter(zotitem__isnull=True).delete()

        # Remove deleted zotero items
        parent_keys = [parent['data']['key'] for parent in parents]
        removed_from_collection = ZotItem.objects.filter(collection=self).exclude(slug__in=parent_keys)
        self.zotitem_set.remove(*removed_from_collection)

        logger.info('updating attachments/notes...')

        for child in children:
            ZotAttachment.update_or_create_from_data(child['data'])

        # Remove deleted attachments/notes or attachments not in DOWNLOAD_FORMATS
        logger.info('cleaning up...')
        child_keys = [child['data']['key'] for child in children]
        try:
            attachments = ZotAttachment.objects.filter(zotitem__collection=self).exclude(
                type__slug__in=settings.DOWNLOAD_FORMATS, key__in=child_keys)
            Item.objects.filter(zotattachment__in=attachments).delete()
            attachments.delete()
        except models.ProtectedError as e:
            handle_protected(e)

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
                try:
                    local_collection.delete()
                except models.ProtectedError as e:
                    handle_protected(e)

        save_collections(False, collections)

    class Meta:
        verbose_name = 'Kollektion'
        verbose_name_plural = 'Kollektionen'


class Author(models.Model):
    name = models.CharField(max_length=255)

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
    amount = models.SmallIntegerField(null=True, blank=True, editable=False)
    price = models.SmallIntegerField(null=True, blank=True, editable=False)
    price_digital = models.SmallIntegerField(null=True, blank=True, editable=False)
    printing = models.BooleanField(default=False, editable=False)

    LIBRARY_ITEMTYPE_DEFAULTS = {
        'shipping': True,
        'request_price': True,
        'additional_supply': False,
        'default_price': None,
        'default_amount': 1,
        'purchasable_at': 0,
        'accessible_at': None,
        'buy_once': False,
        'expires_on_product_date': False,
        'buy_unauthenticated': False,
        'inform_staff': False,
        'title': 'Verkauf',
    }

    PUBLISHING_ITEMTYPE_DEFAULTS = {
        'shipping': True,
        'request_price': True,
        'additional_supply': True,
        'default_price': None,
        'default_amount': 0,
        'purchasable_at': 0,
        'accessible_at': None,
        'buy_once': False,
        'expires_on_product_date': False,
        'buy_unauthenticated': False,
        'inform_staff': False,
        'title': 'Verkauf',
    }

    @property
    def lendings_active(self):
        return self.lending_set.filter(returned__isnull=True)

    @property
    def lendings_possible(self):
        try:
            return self.product.item_set.get(type__title='Leihe').amount - len(self.lendings_active)
        except ObjectDoesNotExist:
            return None

    @property
    def amount_bought(self):
        try:
            local_amount = self.product.item_set.get(type__shipping=True).amount
            return self.amount - local_amount
        except Item.DoesNotExist:
            return None

    @classmethod
    def update_or_create_from_data(cls, data):
        """
        Given API data from Zotero as dict, update or create a ZotItem.
        """
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
            return None

        # Get extra variables
        extra_variables = dict(re.findall(r'{(\w+):\s?(\w+)}', data.get('extra', '')))

        # Get amount
        amount = extra_variables.get('amount')
        if not amount:
            tags = [tag['tag'] for tag in data['tags']]
            owned = any([tag in tags for tag in settings.ZOTERO_OWNER_TAGS])
            if owned:
                excluded = any([tag in tags for tag in settings.ZOTERO_EXCLUDED_TAGS])
                if excluded:
                    amount = 0
                else:
                    amount = 1

        # Get/Set authors
        authors = []
        for creator in data.get('creators', []):
            names = list(filter(None, [creator.get(name_key) for name_key in ['firstName', 'name', 'lastName']]))
            full_name = ' '.join(names)
            author, created = Author.objects.get_or_create(name=full_name)
            authors.append(author)

        slug = data['key']
        item_data = {
            'slug': slug,
            'title': title,
            'published': date,
            'amount': amount,
            'price': extra_variables.get('price'),
            'price_digital': extra_variables.get('price_digital'),
            'printing': bool(extra_variables.get('printing')),
        }

        existing = cls.objects.filter(slug=slug)
        local_amount = existing.get().amount if existing else None
        amount_changed = local_amount is not amount

        zot_item, created = existing.update_or_create(defaults=item_data)
        zot_item.authors.clear()
        zot_item.authors.add(*authors)
        zot_item.update_or_create_purchase_item(amount_changed=amount_changed)

        logger.debug(f'Saved item {zot_item.title}. Created: {created}')
        return zot_item

    @classmethod
    def remove_deleted(cls):
        for item in cls.objects.filter(collection__isnull=True):
            try:
                item.delete()  # Avoid bulk_delete
            except models.ProtectedError as e:
                handle_protected(e)

    def update_or_create_purchase_item(self, amount_changed=False):
        """
        Updates purchasable items for a Zotero Item
        """
        if self.amount is not None:
            if self.printing:
                itemtype, created = ItemType.objects.update_or_create(
                    slug='published_purchase',
                    defaults=self.PUBLISHING_ITEMTYPE_DEFAULTS)
            else:
                itemtype, created = ItemType.objects.update_or_create(
                    slug='library_purchase',
                    defaults=self.LIBRARY_ITEMTYPE_DEFAULTS)

            existing = self.product.item_set.filter(type__shipping=True)

            # Only overwrite amount if changed
            amount = self.amount
            if existing and not amount_changed:
                amount = existing.first().amount

            existing.update_or_create(
                defaults={
                    'product': self.product,
                    'type': itemtype,
                    '_price': self.price,
                    'amount': amount
                })

        else:  # Delete purchase items
            try:
                self.product.item_set.filter(type__shipping=True).delete()
            except models.ProtectedError:
                logger.warning(f'Can not delete item for {self}, has been bought. Setting amount to 0.')
                self.amount = 0
                return self.update_or_create_purchase_item(amount_changed=amount_changed)

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
