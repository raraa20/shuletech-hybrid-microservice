from fastapi import FastAPI
from app.database_mysql import engine, Base
from app.routes import core_routes

# Build our local database tables on execution
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShuleTech Hybrid ERP")

app.include_router(core_routes.router)