from django.db import migrations

PL900_PLAYLIST = 'https://www.youtube.com/playlist?list=PLetRDsPWnHxA'


def set_playlist(apps, schema_editor):
    # Pre-fill the PL-900 playlist so the first sync is one click. Never overwrite one set in BMS.
    Track = apps.get_model('academy', 'Track')
    Track.objects.filter(pk='pl900', video_playlist='').update(video_playlist=PL900_PLAYLIST)


class Migration(migrations.Migration):
    dependencies = [('academy', '0004_track_video_playlist')]
    operations = [migrations.RunPython(set_playlist, migrations.RunPython.noop)]
