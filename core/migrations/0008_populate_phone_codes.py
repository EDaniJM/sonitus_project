from django.db import migrations



def populate_codes(apps, schema_editor):
    Country = apps.get_model('core', 'Country')

    # Diccionario con los códigos de los países que ya tienes
    COUNTRY_CODES = {
        "Antigua and Barbuda": "+1-268",
        "Argentina": "+54",
        "Bahamas": "+1-242",
        "Barbados": "+1-246",
        "Belize": "+501",
        "Bolivia": "+591",
        "Brazil": "+55",
        "Canada": "+1",
        "Chile": "+56",
        "Colombia": "+57",
        "Costa Rica": "+506",
        "Cuba": "+53",
        "Dominica": "+1-767",
        "Ecuador": "+593",
        "El Salvador": "+503",
        "United States": "+1",
        "Grenada": "+1-473",
        "Guatemala": "+502",
        "Guyana": "+592",
        "Haiti": "+509",
        "Honduras": "+504",
        "Jamaica": "+1-876",
        "Mexico": "+52",
        "Nicaragua": "+505",
        "Panama": "+507",
        "Paraguay": "+595",
        "Peru": "+51",
        "Puerto Rico": "+1-787, +1-939",
        "Dominican Republic": "+1-809, +1-829, +1-849",
        "Saint Kitts and Nevis": "+1-869",
        "Saint Vincent and the Grenadines": "+1-784",
        "Saint Lucia": "+1-758",
        "Suriname": "+597",
        "Trinidad and Tobago": "+1-868",
        "Uruguay": "+598",
        "Venezuela": "+58",
    }
    print("\nIniciando actualización de códigos telefónicos...")
    for country_name, phone_code in COUNTRY_CODES.items():
        try:
            # Usamos '__iexact' para que la búsqueda ignore mayúsculas/minúsculas
            country = Country.objects.get(name__iexact=country_name)
            country.phone_code = phone_code
            country.save()
            # Mensaje de éxito
            print(f"  -> Actualizado: {country.name} con el código {phone_code}")
        except Country.DoesNotExist:
            # Mensaje de advertencia si no se encuentra un país
            print(f"  ! ADVERTENCIA: No se encontró el país '{country_name}' en la base de datos.")
    print("Actualización de códigos finalizada.")

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_country_phone_code'), # Revisa que este sea el nombre de tu migración anterior
    ]
    operations = [
        migrations.RunPython(populate_codes),
    ]