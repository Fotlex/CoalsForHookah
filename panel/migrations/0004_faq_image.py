# Generated by Django 5.2.1 on 2025-07-29 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0003_faq'),
    ]

    operations = [
        migrations.AddField(
            model_name='faq',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='media/', verbose_name='Фото/Картинка к ответу'),
        ),
    ]
