# Generated by Django 5.0.6 on 2024-05-27 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_orderitem_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]