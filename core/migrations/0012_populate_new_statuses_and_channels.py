from django.db import migrations

def populate_data(apps, schema_editor):
    # --- Poblar la nueva tabla core_callstatus ---
    CallStatus = apps.get_model('core', 'CallStatus')
    statuses = ['RECEIVED', 'MISSED', 'RETURNED']
    for status_name in statuses:
        CallStatus.objects.get_or_create(name=status_name)

    # --- Añadir nuevas opciones a core_supportchannel ---
    SupportChannel = apps.get_model('core', 'SupportChannel')
    new_channels = [
        {'name': 'Call Center', 'is_call': True},
        {'name': 'Online Meeting', 'is_call': True},
        {'name': 'Training Presential', 'is_call': False},
    ]
    for channel_data in new_channels:
        SupportChannel.objects.get_or_create(
            name=channel_data['name'], 
            defaults={'is_call': channel_data['is_call']}
        )

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_callstatus_alter_country_phone_code_and_more'), 
    ]
    operations = [
        migrations.RunPython(populate_data),
    ]