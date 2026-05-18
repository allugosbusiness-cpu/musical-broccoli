from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deprecated: Use server.api management commands instead'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is deprecated. Use server.api management commands instead.'
        ))
