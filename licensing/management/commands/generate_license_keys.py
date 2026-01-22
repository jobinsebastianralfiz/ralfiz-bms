from django.core.management.base import BaseCommand
from licensing.models import LicenseKey


class Command(BaseCommand):
    help = 'Generate a new RSA key pair for license signing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='RetailEase Pro',
            help='Name for the key pair'
        )
        parser.add_argument(
            '--key-size',
            type=int,
            default=4096,
            help='RSA key size in bits (default: 4096)'
        )

    def handle(self, *args, **options):
        name = options['name']
        key_size = options['key_size']
        
        self.stdout.write(f'Generating {key_size}-bit RSA key pair...')
        
        key_pair = LicenseKey.generate_key_pair(name=name, key_size=key_size)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated key pair!'))
        self.stdout.write(f'ID: {key_pair.id}')
        self.stdout.write(f'Name: {key_pair.name}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('PUBLIC KEY (embed in your Flutter app):'))
        self.stdout.write(key_pair.public_key)
        self.stdout.write('')
        self.stdout.write(self.style.ERROR('PRIVATE KEY (KEEP SECRET - stored in database):'))
        self.stdout.write('The private key is securely stored in the database.')
        self.stdout.write('Access it through Django admin if needed.')
