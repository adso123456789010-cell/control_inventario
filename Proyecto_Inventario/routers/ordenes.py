from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from models.factura import Factura

from core.database import obtener_bd

from models.orden import Orden as OrdenModel
from models.mecanico import Mecanico as MecanicoModel
from models.repuesto import Repuesto as RepuestoModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from models.factura import Factura

from schemas.ordenes import (
    OrdenCreate,
    OrdenPatch,
    OrdenResponse,
    AgregarRepuestoOrden,
    RepuestoEnOrdenResponse
)

from dependencias import verificar_api_key, parametros_paginacion


router = APIRouter(
    prefix="/ordenes",
    tags=["Gestionar ordenes"]
)


@router.get("/", response_model=List[OrdenResponse])
async def obtener_ordenes(
    estado: Optional[str] = None,
    paginacion: dict = Depends(parametros_paginacion),
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).options(
        joinedload(OrdenModel.mecanico)
    )

    if estado:
        sentencia = sentencia.where(
            OrdenModel.estado == estado
        )

    resultado = await db.execute(sentencia)
    ordenes = resultado.scalars().unique().all()

    return ordenes


@router.get("/{orden_id}", response_model=OrdenResponse)
async def obtener_orden_por_id(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = (
        select(OrdenModel)
        .options(joinedload(OrdenModel.mecanico))
        .where(OrdenModel.id == orden_id)
    )

    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )

    return orden


@router.post("/", status_code=201)
async def crear_orden(
    orden: OrdenCreate,
    api_key: str = Depends(verificar_api_key),
    db: AsyncSession = Depends(obtener_bd)
):
    consulta_mec = select(MecanicoModel).where(
        MecanicoModel.id == orden.mecanico_id
    )

    res_mec = await db.execute(consulta_mec)
    mecanico_db = res_mec.scalar_one_or_none()

    if not mecanico_db or not mecanico_db.activo:
        raise HTTPException(
            status_code=400,
            detail=f"El mecanico con el ID {orden.mecanico_id} no existe o está inactivo."
        )

    nueva_orden = OrdenModel(
        **orden.model_dump(),
        costo_reparacion=0,
        estado="En diagnóstico"
    )

    db.add(nueva_orden)

    try:
        await db.commit()
        await db.refresh(nueva_orden)

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al guardar en la base de datos"
        )

    return {
        "mensaje": "Orden creada correctamente",
        "orden": nueva_orden
    }


@router.delete("/{placa}", status_code=204)
async def eliminar_orden(
    placa: str,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).where(
        OrdenModel.placa == placa
    )

    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(
            status_code=404,
            detail="La orden no existe"
        )

    if orden.estado == "Reparada":
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar una orden reparada"
        )

    await db.delete(orden)
    await db.commit()

    return None


@router.patch("/{orden_id}")
async def actualizar_orden(
    orden_id: int,
    datos: OrdenPatch,
    db: AsyncSession = Depends(obtener_bd)
):
    try:
        resultado = await db.execute(
            select(OrdenModel).where(
                OrdenModel.id == orden_id
            )
        )

        orden = resultado.scalar_one_or_none()

        if orden is None:
            raise HTTPException(
                status_code=404,
                detail="Orden no encontrada"
            )

        if orden.estado == "Reparada":
            raise HTTPException(
                status_code=400,
                detail="La orden ya está cerrada o facturada"
            )

        if datos.nuevo_estado == "Reparada":

            resultado = await db.execute(
                select(Factura).where(
                    Factura.orden_id == orden_id
                )
            )

            factura_existente = resultado.scalar_one_or_none()

            if factura_existente:
                raise HTTPException(
                    status_code=400,
                    detail="La orden ya tiene una factura asociada"
                )

            resultado = await db.execute(
                select(OrdenRepuestoModel).where(
                    OrdenRepuestoModel.orden_id == orden_id
                )
            )

            repuestos = resultado.scalars().all()

            subtotal_repuestos = sum(
                item.cantidad * item.precio_unitario_historico
                for item in repuestos
            )

            if datos.mano_obra is not None:
                mano_obra = datos.mano_obra
            elif datos.costo_reparacion is not None:
                mano_obra = datos.costo_reparacion - subtotal_repuestos
            else:
                mano_obra = 0

            if mano_obra < 0:
                raise HTTPException(
                    status_code=400,
                    detail="La mano de obra no puede ser negativa ni inferior al subtotal de repuestos"
                )

            total_neto = subtotal_repuestos + mano_obra

            if total_neto <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede reparar ni facturar una orden con costo cero"
                )

            iva = round(total_neto * 0.19, 2)
            total_pagar = round(total_neto + iva, 2)

            orden.costo_reparacion = total_neto
            orden.estado = "Reparada"

            nueva_factura = Factura(
                orden_id=orden_id,
                subtotal_repuestos=subtotal_repuestos,
                costo_mano_obra=mano_obra,
                iva=iva,
                total_pagar=total_pagar
            )

            db.add(nueva_factura)

        else:
            datos_actualizar = datos.model_dump(
                exclude_unset=True,
                exclude={"mano_obra", "nuevo_estado"}
            )

            for campo, valor in datos_actualizar.items():
                setattr(orden, campo, valor)

            if datos.nuevo_estado is not None:
                orden.estado = datos.nuevo_estado

        await db.commit()
        await db.refresh(orden)

        return {
            "mensaje": "Orden actualizada correctamente",
            "orden_id": orden.id,
            "estado": orden.estado,
            "costo_reparacion": orden.costo_reparacion,
            "factura_generada": datos.nuevo_estado == "Reparada"
        }

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="La orden ya tiene una factura asociada"
        )

    except Exception as error:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar la orden: {str(error)}"
        )


@router.post(
    "/{orden_id}/repuestos",
    status_code=201,
    response_model=RepuestoEnOrdenResponse
)
async def agregar_repuesto_a_orden(
    orden_id: int,
    datos: AgregarRepuestoOrden,
    db: AsyncSession = Depends(obtener_bd)
):
    res_orden = await db.execute(
        select(OrdenModel).where(
            OrdenModel.id == orden_id
        )
    )

    orden_db = res_orden.scalar_one_or_none()

    if not orden_db:
        raise HTTPException(
            status_code=404,
            detail="La orden de servicio no existe"
        )

    if orden_db.estado == "Reparada":
        raise HTTPException(
            status_code=400,
            detail="No se pueden modificar repuestos de una orden ya cerrada/facturada"
        )

    resultado = await db.execute(
        select(Factura).where(
            Factura.orden_id == orden_id
        )
    )

    factura = resultado.scalar_one_or_none()

    if factura is not None:
        raise HTTPException(
            status_code=400,
            detail="No se pueden modificar repuestos de una orden ya cerrada/facturada"
        )

    res_rep = await db.execute(
        select(RepuestoModel).where(
            RepuestoModel.id == datos.repuesto_id
        )
    )

    rep_db = res_rep.scalar_one_or_none()

    if not rep_db:
        raise HTTPException(
            status_code=404,
            detail="El repuesto no existe"
        )

    if rep_db.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. En almacén tengo: {rep_db.stock_actual} y se solicitaron: {datos.cantidad}"
        )

    rep_db.stock_actual -= datos.cantidad

    subtotal = rep_db.precio_venta * datos.cantidad
    orden_db.costo_reparacion += subtotal

    detalle = OrdenRepuestoModel(
        orden_id=orden_db.id,
        repuesto_id=rep_db.id,
        cantidad=datos.cantidad,
        precio_unitario_historico=rep_db.precio_venta
    )

    db.add(detalle)

    try:
        await db.commit()
        await db.refresh(detalle)

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al agregar el repuesto a la orden"
        )

    return detalle