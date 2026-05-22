from django.db import migrations
from decimal import Decimal


def seed_accounts(apps, schema_editor):
    BankAccount = apps.get_model('core', 'BankAccount')
    OpeningBalance = apps.get_model('core', 'OpeningBalance')

    if BankAccount.objects.exists():
        return

    opening = OpeningBalance.objects.order_by('-as_of_date', '-created_at').first()
    cash_open = opening.cash_in_hand if opening else Decimal('0')
    bank_open = opening.cash_in_account if opening else Decimal('0')
    open_date = opening.as_of_date if opening else None

    from django.utils import timezone
    today = timezone.now().date()

    BankAccount.objects.create(
        name='Cash in Hand',
        account_type='cash',
        opening_balance=cash_open,
        opening_date=open_date or today,
        is_cash=True,
        is_primary_bank=False,
        display_order=0,
    )
    BankAccount.objects.create(
        name='Primary Bank Account',
        account_type='bank',
        opening_balance=bank_open,
        opening_date=open_date or today,
        is_cash=False,
        is_primary_bank=True,
        display_order=10,
    )


def unseed_accounts(apps, schema_editor):
    BankAccount = apps.get_model('core', 'BankAccount')
    BankAccount.objects.filter(name__in=['Cash in Hand', 'Primary Bank Account']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_bankaccount_internaltransfer'),
    ]

    operations = [
        migrations.RunPython(seed_accounts, unseed_accounts),
    ]
