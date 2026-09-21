"""Randomización reproducible con parámetros bloqueables.

``randomize(base, seed, lock, layers)`` genera un diseño nuevo a partir de ``seed`` y
conserva de ``base`` todo lo que aparezca en ``lock``. Cada entrada de ``lock`` es una ruta
con puntos sobre el JSON de la configuración: un bloque entero (``palette``, ``frame``), un
campo (``frame.kind``, ``palette.background``) o una opción (``frame.options.motif``).

``layers`` es el atajo inverso: la lista de capas que se aleatorizan, dejando las demás
como estén. ``None`` (el valor por defecto) aleatoriza todas.

No se randomizan ``format``, ``dpi`` ni ``symmetry``: son salida y estructura, no diseño.
"""
import copy
import random
from typing import Iterable

from .config import DorsoConfig, get_path, set_path
from .constants import NO_MODULE, SLOTS
from .errors import ConfigError
from .palettes import random_palette
from .registry import get_module

# Capas que se pueden aleatorizar por separado.
LAYERS = ("palette", "style", *SLOTS)

# Peso relativo con que se elige cada módulo de una ranura. "none" = ranura vacía.
KIND_WEIGHTS = {
    "frame": {"simple": 2, "doble": 3, "geometrico": 3, "ornamentado": 2, NO_MODULE: 0.3},
    "pattern": {"rombos": 3, "celosia": 3, "reticula": 3, "rosetas": 3, "panal": 3, "mudejar": 3,
                "ondas": 2, "arabescos": 2, "guilloche": 2, "espiga": 2, "greca": 2, "entrelazo": 2,
                "damasco": 2, "sembrado": 2, "radial": 1, NO_MODULE: 0.2},
    "medallion": {"circulo": 2, "rombo": 2, "roseta": 2, "estrella": 1, "ovalo": 1, "cuatrilobulo": 1, NO_MODULE: 1},
    "corners": {"cuarto_circulo": 1, "abanico": 1, "roseta": 1, "rombos": 1, "hojas": 1, NO_MODULE: 1.5},
}
STYLE_RANGES = {  # nombre -> (mínimo, máximo, decimales)
    "density": (0.25, 0.85, 2), "scale": (0.8, 1.5, 2), "margin_mm": (2.5, 4.0, 1),
    "line_width_mm": (0.2, 0.35, 2), "corner_radius_mm": (2.5, 3.5, 1),
}


def randomize(base: DorsoConfig, seed: int, lock: Iterable[str] = (),
              layers: Iterable[str] | None = None) -> DorsoConfig:
    rng = random.Random(seed)
    frozen = base.to_dict(full=True)
    lock = set(lock)
    if layers is not None:
        layers = list(layers)
        unknown = [name for name in layers if name not in LAYERS]
        if unknown:
            raise ConfigError(f"capas desconocidas {sorted(unknown)}; válidas: {list(LAYERS)}")
        lock |= {name for name in LAYERS if name not in layers}  # lo no elegido se conserva
    design = {
        "version": frozen["version"], "format": frozen["format"], "size_mm": frozen["size_mm"],
        "dpi": frozen["dpi"], "seed": seed, "symmetry": frozen["symmetry"],
        "palette": random_palette(rng),
        "style": {k: round(rng.uniform(lo, hi), nd) for k, (lo, hi, nd) in STYLE_RANGES.items()},
    }
    for slot in SLOTS:
        design[slot] = _random_slot(slot, frozen[slot], rng, lock)
    for path in sorted(lock):
        try:
            value = copy.deepcopy(get_path(frozen, path))
        except (KeyError, TypeError):
            raise ConfigError(f"lock: la ruta {path!r} no existe en la configuración") from None
        set_path(design, path, value)
    for slot in SLOTS:  # un bloqueo puede dejar opciones de otro módulo
        spec = design[slot]
        if spec["kind"] != NO_MODULE:
            valid = get_module(slot, spec["kind"]).options
            spec["options"] = {k: v for k, v in spec["options"].items() if k in valid}
    return DorsoConfig.from_dict(design)


def _random_slot(slot, frozen, rng, lock):
    if slot in lock or f"{slot}.kind" in lock:
        kind = frozen["kind"]
    else:
        weights = KIND_WEIGHTS[slot]
        kind = rng.choices(list(weights), list(weights.values()))[0]
    options = {}
    if kind != NO_MODULE:
        options = get_module(slot, kind).random_options(rng)
    return {"kind": kind, "enabled": True, "options": options}
