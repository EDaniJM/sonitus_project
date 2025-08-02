# Sonitus Project - Docker Setup

Este documento explica cómo ejecutar el proyecto Sonitus usando Docker y Docker Compose.

## Requisitos Previos

- Docker
- Docker Compose

## Configuración Inicial

1. **Clonar el repositorio** (si no lo has hecho ya):
   ```bash
   git clone <url-del-repositorio>
   cd sonitus_project
   ```

2. **Configurar variables de entorno** (opcional):
   ```bash
   cp env.example .env
   # Editar .env con tus valores específicos
   ```

## Comandos de Docker

### Levantar el proyecto completo
```bash
docker-compose up -d
```

### Ejecutar migraciones
```bash
docker-compose run --rm migrate
```

### Crear superusuario (opcional)
```bash
docker-compose --profile setup run --rm createsuperuser
```

### Ver logs
```bash
docker-compose logs -f web
```

### Detener servicios
```bash
docker-compose down
```

### Detener servicios y eliminar volúmenes
```bash
docker-compose down -v
```

## Acceso a la Aplicación

- **Aplicación web**: http://localhost:8000
- **Base de datos PostgreSQL**: localhost:5432

## Credenciales por Defecto

- **Base de datos**:
  - Usuario: `sonitus_user`
  - Contraseña: `sonitus_password`
  - Base de datos: `sonitus_db`

- **Superusuario Django** (si usas el comando createsuperuser):
  - Usuario: `admin`
  - Contraseña: `admin123`
  - Email: `admin@example.com`

## Estructura de Servicios

### Servicios Principales
- **web**: Aplicación Django (puerto 8000)
- **db**: Base de datos PostgreSQL (puerto 5432)

### Servicios de Configuración
- **migrate**: Ejecuta migraciones de Django
- **createsuperuser**: Crea un superusuario (perfil 'setup')

## Volúmenes

- `postgres_data`: Datos persistentes de PostgreSQL
- `static_volume`: Archivos estáticos de Django

## Desarrollo

Para desarrollo local, puedes montar el código fuente:

```bash
# El código se monta automáticamente en /app dentro del contenedor
# Los cambios se reflejan inmediatamente
```

## Troubleshooting

### Problemas de conexión a la base de datos
```bash
# Verificar que PostgreSQL esté funcionando
docker-compose logs db

# Conectar directamente a la base de datos
docker-compose exec db psql -U sonitus_user -d sonitus_db
```

### Problemas con migraciones
```bash
# Ejecutar migraciones manualmente
docker-compose run --rm web python manage.py migrate

# Crear migraciones si es necesario
docker-compose run --rm web python manage.py makemigrations
```

### Limpiar todo y empezar de nuevo
```bash
docker-compose down -v
docker-compose up -d
docker-compose run --rm migrate
```

## Producción

Para producción, considera:

1. Cambiar `DEBUG=False` en las variables de entorno
2. Usar una SECRET_KEY segura
3. Configurar ALLOWED_HOSTS apropiadamente
4. Usar un servidor web como Nginx
5. Configurar SSL/TLS
6. Usar volúmenes externos para persistencia de datos 