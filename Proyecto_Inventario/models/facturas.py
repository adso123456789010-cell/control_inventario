from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import obtener_bd
from models.factura import Factura

router = APIRouter(prefix="/facturas", tags=["Facturación"])


@router.get("/")
async def obtener_facturas(db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(select(Factura))
    facturas = resultado.scalars().all()

    return [
        {
            "id": factura.id,
            "orden_id": factura.orden_id,
            "fecha_emision": factura.fecha_emision.isoformat() if factura.fecha_emision else None,
            "subtotal_repuestos": factura.subtotal_repuestos,
            "costo_mano_obra": factura.costo_mano_obra,
            "iva": factura.iva,
            "total_pagar": factura.total_pagar
        }
        for factura in facturas
    ]


@router.get("/{factura_id}")
async def obtener_factura(factura_id: int, db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(
        select(Factura).where(Factura.id == factura_id)
    )

    factura = resultado.scalar_one_or_none()

    if not factura:
        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada"
        )

    return {
        "id": factura.id,
        "orden_id": factura.orden_id,
        "fecha_emision": factura.fecha_emision.isoformat() if factura.fecha_emision else None,
        "subtotal_repuestos": factura.subtotal_repuestos,
        "costo_mano_obra": factura.costo_mano_obra,
        "iva": factura.iva,
        "total_pagar": factura.total_pagar
    }


@router.get("/orden/{orden_id}")
async def obtener_factura_por_orden(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    resultado = await db.execute(
        select(Factura).where(Factura.orden_id == orden_id)
    )

    factura = resultado.scalar_one_or_none()

    if not factura:
        raise HTTPException(
            status_code=404,
            detail="Esta orden todavía no tiene factura"
        )

    return {
        "id": factura.id,
        "orden_id": factura.orden_id,
        "fecha_emision": factura.fecha_emision.isoformat() if factura.fecha_emision else None,
        "subtotal_repuestos": factura.subtotal_repuestos,
        "costo_mano_obra": factura.costo_mano_obra,
        "iva": factura.iva,
        "total_pagar": factura.total_pagar
    }