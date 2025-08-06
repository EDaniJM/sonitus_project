# 1. Usar una imagen oficial de Python como base
FROM python:3.10-slim

# 2. Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Crear y establecer el directorio de trabajo
WORKDIR /app

# 4. Instalar dependencias del sistema (si fueran necesarias para psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 5. Instalar dependencias de Python
# Copiamos solo el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código del proyecto
COPY . /app/