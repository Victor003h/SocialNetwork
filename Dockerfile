# Imagen base con Python
FROM python:3.13-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer el puerto Flask
EXPOSE 5000

# Comando para ejecutar la app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
