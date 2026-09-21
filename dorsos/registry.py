"""Registro de módulos por ranura (frame, pattern, medallion, corners).

Para añadir un módulo basta con decorar su clase::

    @register("pattern", "mi_patron")
    class MiPatron(Pattern): ...

y asegurarse de que su fichero se importa (ver ``dorsos/modules/__init__.py``).
"""
from .constants import SLOTS

_REGISTRY: dict[str, dict[str, type]] = {slot: {} for slot in SLOTS}


def register(slot: str, name: str):
    def decorator(cls):
        if name in _REGISTRY[slot]:
            raise ValueError(f"módulo duplicado: {slot}.{name}")
        cls.slot, cls.name = slot, name
        _REGISTRY[slot][name] = cls
        return cls
    return decorator


def kinds(slot: str) -> list[str]:
    from . import modules  # noqa: F401  (importarlos los registra)
    return list(_REGISTRY[slot])


def get_module(slot: str, name: str) -> type:
    from . import modules  # noqa: F401
    try:
        return _REGISTRY[slot][name]
    except KeyError:
        raise KeyError(f"{slot}: módulo desconocido {name!r}; disponibles: {', '.join(_REGISTRY[slot])}") from None
