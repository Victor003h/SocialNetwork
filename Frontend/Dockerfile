# Stage 1: Construcción
FROM node:22-alpine AS build
WORKDIR /app

# Copiamos solo los archivos de dependencias para aprovechar el caché de Docker
COPY package*.json ./
RUN npm install

# Copiamos el resto del código y construimos la app
COPY . .
RUN npm run build

# Stage 2: Servidor de Producción
FROM nginx:stable-alpine
# Copiamos los archivos compilados desde el stage anterior a la ruta de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Exponemos el puerto estándar
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]