from unittest import mock
from datetime import date

from django.test import TestCase
from django.conf import settings

from library.models import Collection, ZotItem


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
    def setUp(self):
        self.mock_settings = {
            'ZOTERO_USER_ID': '',
            'ZOTERO_API_KEY': '',
            'ZOTERO_LIBRARY_TYPE': ''
        }

    def test_sync(self):
        zotero = mock.MagicMock()
        collection = Collection.objects.create(title='test collection 3', slug='testkey4')
        items = [
            {'data': {'key': 'testkey',
                      'itemType': settings.ZOTERO_ITEM_TYPES[0],
                      'title': 'test book',
                      'date': '2018-01-01',
                      'tags': [{'tag': settings.ZOTERO_OWNER_TAGS[0]}],
                      'creators': [{
                        'firstName': 'John',
                        'lastName': 'Smith'
                      }]}},
            {'data': {'key': 'testkey2',
                      'itemType': 'attachment',
                      'title': 'test book pdf',
                      'tags': [],
                      'parentItem': 'testkey',
                      'filename': 'testfile.pdf'}},
        ]
        zotero().everything.return_value = items
        with mock.patch('pyzotero.zotero.Zotero', zotero), self.settings(**self.mock_settings):
            collection.sync()

        testitem = ZotItem.objects.get(slug=items[0]['data']['key'])
        # Test title
        self.assertEqual(testitem.title, items[0]['data']['title'])
        # Test date
        self.assertEqual(testitem.published, date(2018, 1, 1))
        # Test author creation
        self.assertTrue(testitem.authors.filter(name='John Smith'))
        # Test if purchase item and itemtype got created
        self.assertTrue(testitem.product.item_set.filter(type__slug='purchase'))
        # Test if purchase item with attachment and got created
        pdf_item = testitem.product.item_set.get(type__slug='pdf')
        self.assertEqual(pdf_item.attachment.key, items[1]['data']['key'])
