from core.app_settings import get_settings # Modifica model para prueba aqui
from sqlalchemy import Table, create_engine, MetaData
from sqlalchemy.orm import Session
settings = get_settings()

engine = create_engine(f"mysql+mysqlconnector://{settings.MYSQL_DB_USERNAME}:{settings.MYSQL_DB_PASSWORD}@{settings.MYSQL_DB_HOST}:{settings.MYSQL_DB_PORT}/{settings.MYSQL_DB_NAME}")

# Se crean los modelos que estan mapeados en python
#database_models.Base.metadata.create_all(bind = engine)
metadata = MetaData()
# Crea un ob
# Refleja las tablas existentes
metadata.reflect(bind=engine)

def get_table(table_name):
    return metadata.tables[table_name]

def get_engine():
    return engine

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()