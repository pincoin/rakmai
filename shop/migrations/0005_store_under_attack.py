# Generated by Django 2.2.24 on 2021-09-18 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_auto_20210910_2147'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='under_attack',
            field=models.BooleanField(default=False, verbose_name='under attack'),
        ),
    ]