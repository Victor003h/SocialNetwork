import os

class Config:

    DATABASE_URL= os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        # Variables de entorno o valores por defecto
        DB_USER = os.getenv("POSTGRES_USER", "admin")
        DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")
        DB_HOST = os.getenv("DB_HOST", "localhost") ###
        DB_NAME = os.getenv("POSTGRES_DB", "redsocial")

        # URI de conexión
        SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

    # Configuraciones adicionales
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
