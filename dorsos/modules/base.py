"""Base común de los módulos: especificación de opciones, contexto y validación.

Cada módulo declara sus opciones como ``Opt``; de esa declaración salen la validación,
los valores por defecto, la randomización y el listado de ``dorsos modules``.
"""
import random
import re
from dataclasses import dataclass

from ..constants import ROLES
from ..errors import ConfigError
from ..geometry import Rect

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
# Al randomizar, un color solo salta entre estos roles: siempre contrastan con el fondo.
_RANDOM_ROLES = ("primary", "secondary", "accent")


@dataclass(frozen=True)
class Opt:
    """Opción de un módulo.

    ``choices`` limita a una lista; ``lo``/``hi`` a un rango numérico; ``color=True``
    admite un rol de la paleta o un ``#rrggbb``. ``rand=False`` la excluye de la
    randomización y ``rlo``/``rhi`` la limitan a un subrango sensato.
    """
    default: object
    doc: str = ""
    choices: tuple | None = None
    lo: float | None = None
    hi: float | None = None
    color: bool = False
    rand: bool = True
    rlo: float | None = None   # subrango que usa la randomización; por defecto lo/hi
    rhi: float | None = None

    def check(self, name, value):
        if self.color:
            if value in ROLES or (isinstance(value, str) and _HEX.match(value)):
                return value
            raise ConfigError(f"{name}: color inválido {value!r} (rol {ROLES} o #rrggbb)")
        if self.choices is not None:
            if value not in self.choices:
                raise ConfigError(f"{name}: {value!r} no está en {list(self.choices)}")
            return value
        if isinstance(self.default, bool):
            if not isinstance(value, bool):
                raise ConfigError(f"{name}: se esperaba true/false, no {value!r}")
            return value
        if isinstance(self.default, (int, float)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ConfigError(f"{name}: se esperaba un número, no {value!r}")
            if (self.lo is not None and value < self.lo) or (self.hi is not None and value > self.hi):
                raise ConfigError(f"{name}: {value} fuera de [{self.lo}, {self.hi}]")
            return int(value) if isinstance(self.default, int) else float(value)
        return value

    def sample(self, rng: random.Random):
        if self.color:
            return rng.choice(_RANDOM_ROLES) if rng.random() < 0.25 else self.default
        if self.choices is not None:
            return rng.choice(self.choices)
        if isinstance(self.default, bool):
            return rng.random() < 0.5
        lo = self.lo if self.rlo is None else self.rlo
        hi = self.hi if self.rhi is None else self.rhi
        if isinstance(self.default, int) and lo is not None:
            return rng.randint(int(lo), int(hi))
        if isinstance(self.default, float) and lo is not None:
            return round(rng.uniform(lo, hi), 2)
        return self.default


@dataclass
class Context:
    """Datos que recibe un módulo al construirse.

    ``field`` es la zona que le corresponde: para el marco, el interior del margen de
    papel; para patrón, medallón y esquinas, el interior del marco.
    """
    card: Rect
    field: Rect
    palette: dict
    density: float
    scale: float
    line_mm: float
    seed: int
    slot: str = ""

    def color(self, ref: str) -> str:
        return self.palette.get(ref, ref)

    def weight(self, factor: float) -> float:
        """Grosor de trazo en mm como múltiplo del grosor de línea global."""
        return self.line_mm * factor

    def rng(self, *key) -> random.Random:
        """Generador independiente por módulo y clave: activar otros módulos no lo altera."""
        return random.Random(f"{self.seed}/{self.slot}/" + "/".join(map(str, key)))


class Module:
    slot = ""
    name = ""
    doc = ""
    options: dict[str, Opt] = {}

    def __init__(self, given: dict | None = None):
        self.o = self.resolve_options(given or {})

    @classmethod
    def resolve_options(cls, given: dict) -> dict:
        unknown = set(given) - set(cls.options)
        if unknown:
            raise ConfigError(f"{cls.slot}.{cls.name}: opciones desconocidas {sorted(unknown)}; "
                              f"válidas: {sorted(cls.options)}")
        out = {k: opt.default for k, opt in cls.options.items()}
        for k, v in given.items():
            out[k] = cls.options[k].check(f"{cls.slot}.{cls.name}.{k}", v)
        return out

    @classmethod
    def random_options(cls, rng: random.Random) -> dict:
        return {k: opt.sample(rng) for k, opt in cls.options.items() if opt.rand}


@dataclass
class FrameResult:
    """Lo que devuelve un marco: sus primitivas y las formas que delimita.

    ``outer`` es el contorno del campo de color; ``inner`` la zona interior del marco,
    donde se colocan medallón y esquinas. El patrón se recorta a ``inner`` salvo que el
    marco devuelva ``pattern_area``: un ``(contorno, rectángulo)`` propio, que es como los
    marcos con ``bleed`` dejan que el patrón pase por debajo de sus líneas.
    """
    prims: list
    outer: list
    inner: list
    inner_rect: Rect
    pattern_area: tuple | None = None

    @property
    def pattern_clip(self) -> tuple:
        return self.pattern_area[0] if self.pattern_area else self.inner

    @property
    def pattern_rect(self) -> Rect:
        return self.pattern_area[1] if self.pattern_area else self.inner_rect
