
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from routers.ordenes import router as router_ordenes
from routers.mecanicos import router as router_mecanicos
from routers.repuestos import router as router_repuestos

from dependencias import simular_base_datos
from core.config import settings
from core.database import engine, Base

from models.orden import Orden
from models.repuesto import Repuesto
from models.mecanico import Mecanico
from models.orden_repuesto import OrdenRepuesto
from models.factura import Factura


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Conectando con la base de datos y creando las tablas ---")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Base de datos lista.")

    yield

    print("Apagando el servidor y limpiando recursos.")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema de triaje y facturación",
    version="1.0",
    lifespan=lifespan
)


app.include_router(router_mecanicos)
app.include_router(router_ordenes)
app.include_router(router_repuestos)


@app.get("/prueba-yield")
async def probar_yield(conexion: str = Depends(simular_base_datos)):
    print("2. [RUTA] Ejecutando la ruta. Estado:", conexion)
    return {"mensaje": "Revisar consola."}


@app.get("/")
async def ping():
    return {
        "mensaje": f"Bienvenido a {settings.PROJECT_NAME}",
        "db_configurada": True
    }
