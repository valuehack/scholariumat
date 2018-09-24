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
            defaults['public'] = article['fields']['inhalt']
            if article['fields']['inhalt_nur_fuer_angemeldet'] is not None:
                defaults['private'] = article['fields']['inhalt_nur_fuer_angemeldet']
            if article['fields']['inhalt2'] is not None:
                defaults['public2'] = article['fields']['inhalt2']
            if article['fields']['literatur'] is not None:
                defaults['references'] = article['fields']['literatur']

        title = pypandoc.convert(article['fields']['bezeichnung'], 'md', format='html')
        new, created = Article.objects.update_or_create(title=title, defaults=defaults)
        if created:
            logger.debug(f'Created article {new.title}')
