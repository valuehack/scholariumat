from django.core.management.base import BaseCommand
from users.utils import import_from_json as import_users
from blog.utils import import_from_json as import_articles
from events.utils import import_from_json as import_events
from products.utils import download_missing_files, download_old_db


class Command(BaseCommand):
    help = 'Imports all old database data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting full import.'))
        download_old_db()
        import_users()
        import_articles()
        import_events()
        download_missing_files()
        self.stdout.write(self.style.SUCCESS('Import successfully finished.'))
