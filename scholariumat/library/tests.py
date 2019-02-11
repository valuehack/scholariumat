from unittest import mock
from datetime import date

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model

from library.models import Collection, ZotItem, ZotAttachment
from products.models import ItemType, AttachmentType, Purchase, Item, Product
from users.models import Profile


class AttachmentTest(TestCase):
    def setUp(self):
        self.mock_settings = {
            'ZOTERO_USER_ID': '',
            'ZOTERO_API_KEY': '',
            'ZOTERO_LIBRARY_TYPE': ''
        }

    def test_pdf_generation(self):
        product = ZotItem.objects.create(title='testtitle', slug='testkey')
        type = ItemType.objects.create(title='typetitle')
        item = product.product.item_set.create(type=type)
        attachment_type = AttachmentType.objects.create(title='PDF')
        attachment = ZotAttachment.objects.create(key='foo', format='note', type=attachment_type, item=item)

        zotero = mock.MagicMock()
        item = {'data': {'note': 'testtext'}}
        zotero().item.return_value = item
        with mock.patch('pyzotero.zotero.Zotero', zotero), self.settings(**self.mock_settings):
            response = attachment.get()

        self.assertEqual(response.status_code, 200)


class ImportTest(TestCase):
    def setUp(self):
        self.mock_settings = {
            'ZOTERO_USER_ID': '',
            'ZOTERO_API_KEY': '',
            'ZOTERO_LIBRARY_TYPE': ''
        }

    def test_retrieve(self):
        zotero = mock.MagicMock()
        collections = [
            {'data': {'key': 'testkey',
                      'name': 'test collection',
                      'parentCollection': False}},
            {'data': {'key': 'testkey2',
                      'name': 'test collection 2',
                      'parentCollection': 'testkey'}},
            {'data': {'key': 'testkey3',
                      'name': '_hidden collection',
                      'parentCollection': False}},
        ]
        zotero().collections.return_value = collections
        with mock.patch('pyzotero.zotero.Zotero', zotero), self.settings(**self.mock_settings):
            Collection.retrieve()

        # Hidden collection should notbe created
        self.assertFalse(Collection.objects.filter(slug='testkey3'))
        # Test if parent relationship got created
        self.assertEqual(Collection.objects.get(slug='testkey2').parent, Collection.objects.get(slug='testkey'))


class SyncTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mock_settings = {
            'ZOTERO_USER_ID': '',
            'ZOTERO_API_KEY': '',
            'ZOTERO_LIBRARY_TYPE': ''
        }
        cls.zotero = mock.MagicMock()

    def setUp(self):
        self.items = [
            {'data': {'key': 'testkey',
                      'itemType': settings.ZOTERO_ITEM_TYPES[0],
                      'title': 'test book',
                      'date': '2018-01-01',
                      'tags': [{'tag': settings.ZOTERO_OWNER_TAGS[0]}],
                      'creators': [{
                        'firstName': 'John',
                        'lastName': 'Smith'
                      }],
                      'extra': '{price: 12}{price_digital: 6}'}},
            {'data': {'key': 'testkey2',
                      'itemType': 'attachment',
                      'title': 'test book pdf',
                      'tags': [],
                      'parentItem': 'testkey',
                      'filename': 'testfile.pdf'}},
        ]
        self.zotero().everything.return_value = self.items
        self.collection = Collection.objects.create(title='test collection 3', slug='testkey4')
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()

    def tearDown(self):
        Purchase.objects.all().delete()
        ZotItem.objects.all().delete()
        Product.objects.all().delete()
        Item.objects.all().delete()
        ItemType.objects.all().delete()

    def test_retrieval(self):
        testitem = ZotItem.objects.get(slug=self.items[0]['data']['key'])
        self.assertEqual(testitem.title, self.items[0]['data']['title'])
        self.assertEqual(testitem.published, date(2018, 1, 1))
        self.assertTrue(testitem.authors.filter(name='John Smith'))

    def test_item_creation(self):
        # Test if purchase item and itemtype got created
        testitem = ZotItem.objects.get(slug=self.items[0]['data']['key'])
        item = testitem.product.item_set.get(type__slug__contains='purchase')
        self.assertEqual(item.price, 12)
        self.assertEqual(item.amount, 1)

    def test_attachment_creation(self):
        # Test if purchase item with attachment and got created
        self.assertTrue(ZotAttachment.objects.exists())
        testitem = ZotItem.objects.get(slug=self.items[0]['data']['key'])
        item = testitem.product.item_set.get(type__slug='pdf')
        self.assertEqual(item.attachments[0].key, self.items[1]['data']['key'])
        self.assertEqual(item.price, 6)
        self.assertEqual(item.amount, None)

    def test_removed_from_all_collections(self):
        self.zotero().everything.return_value = []
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        ZotItem.remove_deleted()
        self.assertFalse(ZotItem.objects.exists())

    def test_removed_from_collection(self):
        collection2 = Collection.objects.create(title='test collection 4', slug='testkey5')
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            collection2.sync()
        self.zotero().everything.return_value = []
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        ZotItem.remove_deleted()

        self.assertTrue(ZotItem.objects.exists())
        self.assertFalse(bool(self.collection.zotitem_set.all()))
        self.assertTrue(bool(collection2.zotitem_set.all()))

    def test_deletion(self):
        self.zotero().everything.return_value = [self.items[0]]
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        self.assertFalse(ZotAttachment.objects.exists())
        self.assertFalse(Item.objects.filter(type__slug='pdf').exists())

    def test_override(self):
        self.zotero().everything.return_value[0]['data']['extra'] = '{amount: 2}'
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        purchase_item = Item.objects.get(type__slug__contains='purchase')
        self.assertEqual(purchase_item.amount, 2)
        self.assertEqual(purchase_item.price, None)

        pdf_item = Item.objects.get(type__slug='pdf')
        self.assertEqual(pdf_item.price, 5)

    def test_amount_change(self):
        purchase_item = Item.objects.get(type__slug__contains='purchase')
        purchase_item.sell(1)  # Bought 1 time
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        purchase_item.refresh_from_db()
        self.assertEqual(purchase_item.amount, 0)

    def test_amount_override(self):
        purchase_item = Item.objects.get(type__slug__contains='purchase')
        purchase_item.sell(1)  # Bought 1 time
        self.zotero().everything.return_value[0]['data']['extra'] = '{amount: 4}'
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        purchase_item.refresh_from_db()
        self.assertEqual(purchase_item.amount, 4)

    def test_purchase_protection(self):
        purchase_item = Item.objects.get(type__slug__contains='purchase')
        user = get_user_model().objects.create(email='a.b@c.de')
        profile = Profile.objects.create(user=user)
        purchase = Purchase.objects.create(profile=profile, item=purchase_item)
        purchase.execute()
        self.zotero().everything.return_value[0]['data']['tags'] = []
        with mock.patch('pyzotero.zotero.Zotero', self.zotero), self.settings(**self.mock_settings):
            self.collection.sync()
        self.assertTrue(Item.objects.filter(type__slug__contains='purchase').exists())
