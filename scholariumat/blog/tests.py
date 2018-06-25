from unittest import mock
from requests.models import Response

from django.test import TestCase

# from pyzotero import zotero

from blog.models import Article


class ArticleTest(TestCase):
    def setUp(self):
        self.article = Article.objects.create(title='Testarticle', text='test.')
        self.mock_settings = {
            'BUFFER_SITE_IDS': '',
            'BUFFER_ACCESS_TOKEN': ''
        }

    def test_buffer(self):
        '''
        Test if Buffer publishing runs through.
        '''
        response = Response()
        response.status_code = 200
        mocked_post = mock.MagicMock(return_value=response)
        with mock.patch('requests.post', mocked_post), self.settings(**self.mock_settings):
            self.article.buffer_publish()


class SyncTest(TestCase):
    def setUp(self):
        self.mock_settings = {
            'ZOTERO_API_KEY': '',
            'ZOTERO_USER_ID': '',
            'ZOTERO_LIBRARY_TYPE': ''
        }
        self.articles = {
        
        }

    def test_sync(self):
        zot = mock.MagicMock(return_value=self.articles)
        with mock.patch('zot', zot), self.settings(**self.mock_settings):
            Article.sync_articles()
