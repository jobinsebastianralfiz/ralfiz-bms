from django.core.management.base import BaseCommand

from shopmanager_licensing.signing import new_key_pair


class Command(BaseCommand):
    help = "Generate the Ed25519 key pair that signs Shop Manager licence tokens."

    def handle(self, *args, **options):
        private, public = new_key_pair()
        self.stdout.write("Set on the licence server only (Railway variables), never commit it:")
        self.stdout.write(f"  SHOPMANAGER_LICENSE_SIGNING_KEY={private}")
        self.stdout.write("Put in each Shop Manager install (.env LICENSE_PUBLIC_KEY), or in its settings default:")
        self.stdout.write(f"  {public}")
