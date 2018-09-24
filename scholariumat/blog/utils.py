import json
import logging
import pypandoc

from django.conf import settings

from .models import Article


logger = logging.getLogger(__name__)


def import_from_json():
    database = json.load(open(settings.ROOT_DIR.path('db.json')))

    # Articles
    logger.info('Importing articles...')

    articles = [i for i in database if i['model'] == 'Scholien.artikel']
    md_articles = [i for i in database if i['model'] == 'Scholien.markdownartikel']

    for article in articles:
        md_article = next((i for i in md_articles if i['fields']['artikel'] == article['pk']), None)

        defaults = {
            'publish_priority': article['fields']['prioritaet'],
            'publish_date': article['fields']['datum_publizieren']
        }

        if md_article:
            defaults['text'] = md_article['fields']['text']
        else:
            text = [pypandoc.convert(article['fields']['inhalt'], 'md', format='html')]
            if article['fields']['inhalt_nur_fuer_angemeldet'] is not None:
                text.append(pypandoc.convert(article['fields']['inhalt_nur_fuer_angemeldet'], 'md', format='html'))
            if article['fields']['inhalt2'] is not None:
                text.append(pypandoc.convert(article['fields']['inhalt2'], 'md', format='html'))

            defaults['text'] = '\n\n<<<\n\n'.join(text)

        title = pypandoc.convert(article['fields']['bezeichnung'], 'md', format='html')
        new, created = Article.objects.update_or_create(title=title, defaults=defaults)
        if created:
            logger.debug(f'Created article {new.title}')
