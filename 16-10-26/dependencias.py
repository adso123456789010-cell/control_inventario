from fastapi import Header, HTTPException


def verificar_gerente(
    x_role: str = Header(..., alias="X-Role")
):

    if x_role != "Gerente":

        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Solo el Gerente tiene permisos."
        )
    return x_role

def verificar_auditor(
    x_role: str = Header(..., alias="X-Role")
):
    if x_role not in ["Gerente", "Auditor"]:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Se requiere Gerente o Auditor."
        )
    return x_role