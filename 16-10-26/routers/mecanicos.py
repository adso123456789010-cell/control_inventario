from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
import json
import uuid
from schemas2.mecanicos import MecanicoCreate
from dependencias import verificar_gerente, verificar_auditor


router = APIRouter(
    prefix="/mecanicos",
    tags=["Mecanicos"]
)
ARCHIVO = Path(__file__).resolve().parent.parent / "mecanicos.json"
def leer_mecanicos():
    if not ARCHIVO.exists():
        ARCHIVO.write_text("[]", encoding="utf-8")
    with open(ARCHIVO, "r", encoding="utf-8") as archivo:
        return json.load(archivo)
def guardar_mecanicos(mecanicos):
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(
            mecanicos,
            archivo,
            indent=4,
            ensure_ascii=False
        )
@router.get("")
def listar_mecanicos(
    rol: str = Depends(verificar_auditor)
):
    mecanicos = leer_mecanicos()
    return {
        "mensaje": "Lista de mecanicos",
        "total": len(mecanicos),
        "mecanicos": mecanicos
    }
@router.post("")
def crear_mecanico(
    mecanico: MecanicoCreate,
    rol: str = Depends(verificar_gerente)
):
    mecanicos = leer_mecanicos()
    nuevo_mecanico = {
        "id": str(uuid.uuid4()),
        "nombre": mecanico.nombre,
        "especialidad": mecanico.especialidad,
        "salario": mecanico.salario
    }
    mecanicos.append(nuevo_mecanico)
    guardar_mecanicos(mecanicos)
    return {
        "mensaje": "Mecanico creado exitosamente",
        "mecanico": nuevo_mecanico
    }
@router.delete("/{id}")
def eliminar_mecanico(
    id: str,
    rol: str = Depends(verificar_gerente)
):
    mecanicos = leer_mecanicos()
    mecanico_encontrado = next(
        (m for m in mecanicos if m["id"] == id),
        None
    )

    if mecanico_encontrado is None:

        raise HTTPException(
            status_code=404,
            detail="Mecanico no encontrado"
        )

    mecanicos.remove(mecanico_encontrado)

    guardar_mecanicos(mecanicos)

    return {
        "mensaje": "Mecanico eliminado exitosamente",
        "mecanico": mecanico_encontrado
    }