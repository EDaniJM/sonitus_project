from django.db import migrations

def create_groups(apps, schema_editor):
    """
    Crea los grupos de usuarios (roles) "Agent" y "Supervisor"
    y les asigna sus permisos iniciales.
    """
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # --- 1. Obtener todos los permisos necesarios de forma segura ---

    # Permisos para el modelo Support (crear, editar, ver)
    agent_permissions = []
    supervisor_permissions = []
    
    # Intentar obtener permisos de Support de forma segura
    for codename in ['add_support', 'change_support', 'view_support']:
        try:
            permission = Permission.objects.get(codename=codename)
            agent_permissions.append(permission)
            if codename == 'view_support':
                supervisor_permissions.append(permission)
        except Permission.DoesNotExist:
            # Si el permiso no existe, se omite para no causar un error.
            pass
    
    # Permiso personalizado para recargar créditos
    try:
        recharge_credit = Permission.objects.get(codename='can_recharge_credit')
        agent_permissions.append(recharge_credit)
    except Permission.DoesNotExist:
        # Si el permiso no existe, se omite para no causar un error.
        pass

    # --- 2. Crear el rol "Agent" y asignar permisos ---
    agent_group, created = Group.objects.get_or_create(name='Agent')
    if agent_permissions:
        agent_group.permissions.set(agent_permissions)

    # --- 3. Crear el rol "Supervisor" y asignar permisos ---
    supervisor_group, created = Group.objects.get_or_create(name='Supervisor')
    if supervisor_permissions:
        supervisor_group.permissions.set(supervisor_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_creditbalance_options'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]



