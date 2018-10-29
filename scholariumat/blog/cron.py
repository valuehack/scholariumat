import logging
import time

from django_cron import CronJobBase, Schedule

from .models import Article


logger = logging.getLogger(__name__)


class ArticleSync(CronJobBase):  # NOT IN USE!
    RUN_AT_TIMES = ['04:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'Zotero Import Cronjob'

    def do(self):
        logger.info('Running blog article synchronisation job...')
        start = time.time()
        Article.sync_articles()
        end = time.time()
        logger.info('Blog article synchronisation job finished. Took {} seconds.'.format(int(end - start)))


class ArticlePublish(CronJobBase):
    RUN_AT_TIMES = ['04:30']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'Article publish Cronjob'

    def do(self):
        logger.info('Looking for articles to publish...')
        Article.cron_publish()
