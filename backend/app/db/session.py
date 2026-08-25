from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Conexion de owner/admin: Alembic, seed_tenant, import_plan_cuentas, y el
# lookup de usuario en auth (necesita ver todos los tenants antes de saber
# a cual pertenece quien inicia sesion -- ver nota en app/core/deps.py).
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Conexion de runtime: corre como app_user, restringida por RLS. Todo
# endpoint de negocio que ya conoce el tenant (post-login) debe usar esta.
app_engine = create_engine(settings.app_database_url)
AppSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)
