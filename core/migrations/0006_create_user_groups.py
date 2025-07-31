from django.db import migrations

def create_groups(apps, schema_editor):
    """
    Crea los grupos de usuarios (roles) "Agent" y "Supervisor"
    y les asigna sus permisos iniciales.
    """
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # --- 1. Obtener todos los permisos necesarios ---

    # Permisos para el modelo Support (crear, editar, ver)
    add_support = Permission.objects.get(codename='add_support')
    change_support = Permission.objects.get(codename='change_support')
    view_support = Permission.objects.get(codename='view_support')
    
    # Permiso personalizado para recargar créditos
    try:
        recharge_credit = Permission.objects.get(codename='can_recharge_credit')
    except Permission.DoesNotExist:
        # Si el permiso no existe, se omite para no causar un error.
        recharge_credit = None


    # --- 2. Crear el rol "Agent" y asignar permisos ---
    # Puede hacer todo excepto recargar créditos.
    agent_group, created = Group.objects.get_or_create(name='Agent')
    agent_permissions = [
        add_support,
        change_support,
        view_support,
    ]
    agent_group.permissions.set(agent_permissions)


    # --- 3. Crear el rol "Supervisor" y asignar permisos ---
    supervisor_group, created = Group.objects.get_or_create(name='Supervisor')
    supervisor_permissions = [
        view_support,
    ]
    supervisor_group.permissions.set(supervisor_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_creditbalance_options'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]



