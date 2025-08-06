# nginx/Dockerfile

# Usar la imagen oficial de Nginx
FROM nginx:stable-alpine

# Eliminar la configuración por defecto de Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar nuestra configuración personalizada
COPY nginx.conf /etc/nginx/conf.d