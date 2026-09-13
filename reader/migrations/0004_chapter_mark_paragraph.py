from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reader', '0003_chapter_mark_percent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chapter',
            name='mark_percent',
        ),
        migrations.AddField(
            model_name='chapter',
            name='mark_paragraph',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='İşaretlediğin paragraf',
                help_text="Bu bölüm içinde elle bırakılan işaretin paragraf sırası (0'dan başlar)"),
        ),
        migrations.RemoveField(
            model_name='book',
            name='last_scroll_percent',
        ),
    ]
