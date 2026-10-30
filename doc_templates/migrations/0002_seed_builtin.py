from django.db import migrations


def seed(apps, schema_editor):
    from doc_templates.builtin import sync

    sync(apps.get_model("doc_templates", "Template"))


class Migration(migrations.Migration):
    dependencies = [("doc_templates", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
