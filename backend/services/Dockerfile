FROM python:3.11-slim

WORKDIR /app

COPY ./services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


ENV PYTHONPATH=/app

RUN mkdir -p /app/certs

EXPOSE 5000

CMD ["python", "./services/api_gateway.py"]