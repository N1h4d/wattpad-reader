from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reader', '0002_book_reading_progress'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapter',
            name='mark_percent',
            field=models.FloatField(
                default=0, verbose_name='İşaretlediğin yer (%)',
                help_text='Bu bölüm içinde elle bırakılan işaretin sayfa yüzdesi'),
        ),
        migrations.AddField(
            model_name='chapter',
            name='marked_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='İşaretleme zamanı'),
        ),
    ]
