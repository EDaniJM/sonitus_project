# Generated by Django 5.2.4 on 2025-07-21 00:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_client_email_alter_client_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='phone_code',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
