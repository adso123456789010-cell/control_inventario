from pydantic import BaseModel, Field, model_validator
from typing import Optional

class OrdenCreate(BaseModel):
    placa: str = Field(
        ...,
        min_length=5,
        max_length=6,
        description="Placa de la moto (sin espacios)"
    )

    modelo: str = Field(...)

    falla_reportada: str = Field(...)

    mecanico_id: int

class OrdenUpdate(BaseModel):
    nuevo_estado: str = Field(...)

    costo_reparacion: float = Field(..., ge=0)

    @model_validator(mode="after")
    def validar_costo_reparacion(self):

        self.nuevo_estado = self.nuevo_estado.strip().capitalize()

        if (
            self.nuevo_estado == "Reparada"
            and self.costo_reparacion == 0
        ):
            raise ValueError(
                "No se puede marcar como reparada "
                "sin asignar un costo mayor a cero."
            )

        return self

class OrdenPatch(BaseModel):

    nuevo_estado: Optional[str] = Field(
        None,
        description="Ej: En diagnóstico, Reparada, Entregada"
    )

    costo_reparacion: Optional[float] = Field(
        None,
        ge=0
    )

    mano_obra: Optional[float] = Field(
        None,
        ge=0,
        description="Valor cobrado por el trabajo del mecánico"
    )

    falla_reportada: Optional[str] = None

    @model_validator(mode="after")
    def normalizar_estado(self):

        if self.nuevo_estado is not None:
            self.nuevo_estado = self.nuevo_estado.strip().capitalize()

        return self


class MecanicoResumen(BaseModel):

    id: int
    nombre_completo: str
    especialidad: Optional[str] = None

    model_config = {"from_attributes": True}

class OrdenResponse(BaseModel):

    id: int
    placa: str
    modelo: str

    falla_reportada: Optional[str] = None

    estado: str

    costo_reparacion: float

    mecanico: Optional[MecanicoResumen] = None

    model_config = {"from_attributes": True}
    
class AgregarRepuestoOrden(BaseModel):

    repuesto_id: int

    cantidad: int = Field(
        ...,
        gt=0,
        description="Debe agregar al menos 1 unidad"
    )
class RepuestoEnOrdenResponse(BaseModel):

    id: int
    repuesto_id: int
    cantidad: int
    precio_unitario_historico: float

    model_config = {"from_attributes": True}