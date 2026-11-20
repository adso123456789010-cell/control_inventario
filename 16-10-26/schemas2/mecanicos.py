from pydantic import BaseModel


class MecanicoCreate(BaseModel):
    nombre: str
    especialidad: str
    salario: float