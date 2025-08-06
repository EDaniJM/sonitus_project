from django.db import migrations

def create_groups(apps, schema_editor):
    """
    Crea los grupos de usuarios (roles) y les asigna sus permisos iniciales de forma segura.
    """
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # --- 1. Asegurarse de que los permisos para el modelo Support existan ---
    # Al obtener el ContentType, Django crea los permisos si no existen.
    try:
        support_content_type = ContentType.objects.get(
            app_label='core',
            model='support'
        )
    except ContentType.DoesNotExist:
        print("\nADVERTENCIA: No se encontró el ContentType para el modelo Support. Omitiendo la asignación de permisos.")
        return # Salimos de la función si el modelo no existe

    # --- 2. Obtener los permisos necesarios ---
    permissions_to_assign = {
        'Agent': ['add_support', 'change_support', 'view_support'],
        'Supervisor': ['view_support']
    }

    for group_name, permission_codenames in permissions_to_assign.items():
        group, created = Group.objects.get_or_create(name=group_name)
        permissions = []
        for codename in permission_codenames:
            try:
                # Buscamos el permiso asociado al modelo Support
                permission = Permission.objects.get(
                    content_type=support_content_type,
                    codename=codename
                )
                permissions.append(permission)
            except Permission.DoesNotExist:
                print(f"\nADVERTENCIA: El permiso '{codename}' no fue encontrado. Omitiendo.")
        
        group.permissions.set(permissions)
        if created:
            print(f"\n -> Grupo '{group_name}' creado exitosamente.")
        print(f" -> Permisos asignados a '{group_name}': {[p.codename for p in permissions]}")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_creditbalance_options'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]

