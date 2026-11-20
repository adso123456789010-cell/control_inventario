from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(6), nullable=False, index=True)
    modelo = Column(String(100), nullable=False)
    falla_reportada = Column(Text, nullable=False)
    estado = Column(String(50), nullable=False, default="En diagnóstico")
    costo_reparacion = Column(Float, nullable=False, default=0.0)

    mecanico_id = Column(Integer, ForeignKey("mecanicos.id"), nullable=False)

    mecanico = relationship("Mecanico")
    repuestos = relationship(
        "OrdenRepuesto",
        back_populates="orden",
        cascade="all, delete-orphan"
    )
    factura = relationship(
        "Factura",
        back_populates="orden",
        uselist=False,
        cascade="all, delete-orphan"
    )