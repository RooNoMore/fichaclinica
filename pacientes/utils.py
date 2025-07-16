import re


def normalizar_rut(rut: str) -> str:
    """Normaliza un RUT removiendo puntos y guiones y formateando
    como ``XX.XXX.XXX-Y``.
    Si no se puede parsear, retorna la cadena original.
    """
    if not rut:
        return ""
    # Remover todo menos digitos y k/K
    clean = re.sub(r"[^0-9kK]", "", rut)
    if not clean:
        return rut
    cuerpo, dv = clean[:-1], clean[-1].upper()
    try:
        cuerpo_int = int(cuerpo)
    except ValueError:
        return rut
    cuerpo_formateado = f"{cuerpo_int:,}".replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"
