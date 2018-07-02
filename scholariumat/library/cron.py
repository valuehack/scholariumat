import logging
import time

from django_cron import CronJobBase, Schedule

from .models import Collection


logger = logging.getLogger(__name__)


class ZoteroSync(CronJobBase):
    RUN_AT_TIMES = ['04:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'Zotero Import Cronjob'

    def do(self):
        logger.info('Running Zotero synchronisation job...')
        start = time.time()
        Collection.retrieve()
        for collection in Collection.objects.all():
            collection.sync()
        end = time.time()
        logger.info('Zotero synchronisation job finished. Took {} seconds.'.format(int(end - start)))
