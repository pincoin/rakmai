# Generated by Django 2.2.13 on 2020-06-06 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posttag',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='name'),
        ),
    ]
