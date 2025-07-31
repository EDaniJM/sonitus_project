from django.db import migrations

# --- Listas de Datos ---

CLIENT_TYPES = [
    'Installer', 'Distributor', 'End Customer'
]

SUPPORT_CHANNELS = [
    {'name': 'Call by WhatsApp', 'is_call': True},
    {'name': 'Messages by WhatsApp', 'is_call': False},
    {'name': 'Email', 'is_call': False},
    {'name': 'WeChat', 'is_call': False},
    {'name': 'Messages by  FreshDesk', 'is_call': False},
    {'name': 'Call Center', 'is_call': True},
    {'name': 'Online Meeting', 'is_call': True},
    {'name': 'Training Presential', 'is_call': False},
]

CALL_STATUSES = ['RECEIVED', 'MISSED', 'RETURNED']

COUNTRIES = {
    "Antigua and Barbuda": "+1-268", "Argentina": "+54", "Bahamas": "+1-242",
    "Barbados": "+1-246", "Belize": "+501", "Bolivia": "+591", "Brazil": "+55",
    "Canada": "+1", "Chile": "+56", "Colombia": "+57", "Costa Rica": "+506",
    "Cuba": "+53", "Dominica": "+1-767", "Ecuador": "+593", "El Salvador": "+503",
    "United States": "+1", "Grenada": "+1-473", "Guatemala": "+502", "Guyana": "+592",
    "Haiti": "+509", "Honduras": "+504", "Jamaica": "+1-876", "Mexico": "+52",
    "Nicaragua": "+505", "Panama": "+507", "Paraguay": "+595", "Peru": "+51",
    "Puerto Rico": "+1-787, +1-939", "Dominican Republic": "+1-809, +1-829, +1-849",
    "Saint Kitts and Nevis": "+1-869", "Saint Vincent and the Grenadines": "+1-784",
    "Saint Lucia": "+1-758", "Suriname": "+597", "Trinidad and Tobago": "+1-868",
    "Uruguay": "+598", "Venezuela": "+58",
}

def populate_data(apps, schema_editor):
    """
    Puebla todas las tablas de catálogo con los datos iniciales.
    """
    ClientType = apps.get_model('core', 'ClientType')
    for name in CLIENT_TYPES:
        ClientType.objects.get_or_create(name=name)

    SupportChannel = apps.get_model('core', 'SupportChannel')
    for channel_data in SUPPORT_CHANNELS:
        SupportChannel.objects.get_or_create(name=channel_data['name'], defaults={'is_call': channel_data['is_call']})

    CallStatus = apps.get_model('core', 'CallStatus')
    for name in CALL_STATUSES:
        CallStatus.objects.get_or_create(name=name)

    Country = apps.get_model('core', 'Country')
    for country_name, phone_code in COUNTRIES.items():
        Country.objects.get_or_create(name=country_name, defaults={'phone_code': phone_code})

    CreditBalance = apps.get_model('core', 'CreditBalance')
    if not CreditBalance.objects.exists():
        CreditBalance.objects.create(remaining_minutes=3000)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_data),
    ]