# Generated by Django 5.2.4 on 2025-07-22 03:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_country_phone_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'verbose_name': 'Call Status',
                'verbose_name_plural': 'Call Statuses',
            },
        ),
        migrations.AlterField(
            model_name='country',
            name='phone_code',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='support',
            name='call_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.callstatus'),
        ),
    ]
