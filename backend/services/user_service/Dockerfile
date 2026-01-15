FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=secret
ENV DB_HOST=localhost
ENV POSTGRES_DB=user_db

EXPOSE 5002

CMD ["python", "app.py"]
