FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias
COPY ./services/auth_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY . .


# Variables por defecto 
ENV PYTHONPATH=/app
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=secret
ENV DB_HOST=localhost
ENV POSTGRES_DB=auth_db
ENV JWT_SECRET_KEY=supersecretkey

RUN mkdir -p /app/certs

EXPOSE 5001

CMD ["python", "./services/auth_service/app.py"]
