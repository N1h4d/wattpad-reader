import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='last_scroll_percent',
            field=models.FloatField(default=0, verbose_name='Kalınan yer (%)'),
        ),
        migrations.AddField(
            model_name='book',
            name='last_read_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='Son okuma zamanı'),
        ),
        migrations.AddField(
            model_name='book',
            name='last_chapter',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+', to='reader.chapter',
                verbose_name='Kalınan bölüm',
            ),
        ),
    ]
