from django.db import migrations

def create_balance(apps, schema_editor):
    CreditBalance = apps.get_model('core', 'CreditBalance')
    # Creamos la única fila que existirá para el saldo
    CreditBalance.objects.create(remaining_minutes=3000)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0013_creditbalance'), # Revisa que sea el nombre de tu migración anterior
    ]
    operations = [
        migrations.RunPython(create_balance),
    ]