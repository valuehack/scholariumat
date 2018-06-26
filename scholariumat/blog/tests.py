from unittest import mock
from requests.models import Response

from django.test import TestCase

from blog.models import Article


class BufferTest(TestCase):
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
