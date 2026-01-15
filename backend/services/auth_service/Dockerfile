FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY . .

# Variables por defecto 
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=secret
ENV DB_HOST=localhost
ENV POSTGRES_DB=auth_db
ENV JWT_SECRET_KEY=supersecretkey

EXPOSE 5001

CMD ["python", "app.py"]
