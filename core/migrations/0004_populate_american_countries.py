from django.db import migrations

def populate_countries(apps, schema_editor):
    """
    Puebla la tabla core_country con los países de América.
    """
    Country = apps.get_model('core', 'Country')

    american_countries = [
        "Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize",
        "Bolivia", "Brazil", "Canada", "Chile", "Colombia", "Costa Rica",
        "Cuba", "Dominica", "Ecuador", "El Salvador", "United States",
        "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica",
        "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Puerto Rico",
        "Dominican Republic", "Saint Kitts and Nevis",
        "Saint Vincent and the Grenadines", "Saint Lucia", "Suriname",
        "Trinidad and Tobago", "Uruguay", "Venezuela"
    ]

    for country_name in american_countries:
        # Usamos get_or_create para no duplicar países si ya existen
        Country.objects.get_or_create(name=country_name)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_populate_initial_data'), # Revisa que este sea el nombre de tu migración anterior
    ]

    operations = [
        migrations.RunPython(populate_countries),
    ]