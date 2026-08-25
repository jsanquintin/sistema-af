from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    # Conexion separada para el runtime de la app: corre como app_user
    # (no owner), asi FORCE ROW LEVEL SECURITY realmente aplica. Alembic y
    # los scripts de admin (seed_tenant, import_plan_cuentas) usan
    # database_url a proposito -- necesitan visibilidad cross-tenant.
    app_database_url: str
    environment: str = "development"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8


settings = Settings()
