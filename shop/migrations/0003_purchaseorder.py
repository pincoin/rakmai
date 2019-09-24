# Generated by Django 2.2.4 on 2019-09-23 10:23

from decimal import Decimal
from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_auto_20190922_1713'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('is_removed', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=255, verbose_name='purchase order title')),
                ('content', models.TextField(verbose_name='purchase order content')),
                ('bank_account', models.CharField(blank=True, max_length=255, null=True, verbose_name='purchase order bank account')),
                ('amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=11, verbose_name='purchase order amount')),
            ],
            options={
                'verbose_name': 'purchase order',
                'verbose_name_plural': 'purchase order',
            },
        ),
    ]