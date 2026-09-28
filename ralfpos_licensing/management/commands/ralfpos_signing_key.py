from django.core.management.base import BaseCommand

from ralfpos_licensing.signing import new_key_pair


class Command(BaseCommand):
    help = "Generate the Ed25519 key pair that signs RalfPOS licence tokens."

    def handle(self, *args, **options):
        private, public = new_key_pair()
        self.stdout.write("Set on the licence server only (Railway variables), never commit it:")
        self.stdout.write(f"  RALFPOS_LICENSE_SIGNING_KEY={private}")
        self.stdout.write("Put in RalfPOS (settings RALFPOS_LICENSE_PUBLIC_KEY):")
        self.stdout.write(f"  {public}")
