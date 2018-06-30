import logging

from django_cron import CronJobBase, Schedule

from .models import Collection


logger = logging.getLogger(__name__)


class cron_zotero(CronJobBase):
    RUN_AT_TIMES = ['04:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'Zotero Import Cronjob'

    def do(self):
        logger.info('Running Zotero synchronisation job...')
        Collection.retrieve()
        for collection in Collection.objects.all():
            collection.sync()
        logger.info('Zotero synchronisation job finished.')
