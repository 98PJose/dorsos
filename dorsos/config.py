"""Configuración del generador: dataclasses serializables a JSON y validación estricta."""
import copy
import json
from dataclasses import dataclass, field, fields
from pathlib import Path

from .constants import (CONFIG_VERSION, CUSTOM_FORMAT, DEFAULT_DPI, FORMATS, MAX_DPI, MAX_SIZE_MM, MIN_DPI,
                        MIN_SIZE_MM, NO_MODULE, SLOTS, STYLE_LIMITS)
from .errors import ConfigError
from .modules.base import Opt


@dataclass
class Palette:
    background: str = "#c8102e"   # fondo del campo, dentro del marco
    primary: str = "#ffffff"      # trazo principal
    secondary: str = "#8a0b20"    # rellenos y tono medio
    accent: str = "#f2c14e"       # detalles puntuales
    paper: str = "#ffffff"        # margen de papel de la carta


@dataclass
class Style:
    density: float = 0.5          # 0..1: cantidad de detalle dentro de cada motivo
    scale: float = 1.0            # multiplicador del tamaño de los motivos
    margin_mm: float = 3.0        # margen de papel hasta el campo
    line_width_mm: float = 0.25   # grosor base de línea
    corner_radius_mm: float = 3.0  # redondeo de la carta; 0 = esquinas rectas


@dataclass
class Symmetry:
    bilateral: bool = True        # espejo izquierda-derecha
    rotational_180: bool = True   # giro de 180° alrededor del centro


@dataclass
class ModuleSpec:
    kind: str = NO_MODULE
    enabled: bool = True
    options: dict = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.enabled and self.kind != NO_MODULE


@dataclass
class DorsoConfig:
    version: int = CONFIG_VERSION
    format: str = "poker"
    size_mm: tuple | None = None  # solo con format="custom"
    dpi: int = DEFAULT_DPI
    seed: int = 0
    palette: Palette = field(default_factory=Palette)
    style: Style = field(default_factory=Style)
    symmetry: Symmetry = field(default_factory=Symmetry)
    frame: ModuleSpec = field(default_factory=lambda: ModuleSpec("doble"))
    pattern: ModuleSpec = field(default_factory=lambda: ModuleSpec("rombos"))
    medallion: ModuleSpec = field(default_factory=ModuleSpec)
    corners: ModuleSpec = field(default_factory=ModuleSpec)

    @property
    def size(self) -> tuple[float, float]:
        return tuple(self.size_mm) if self.format == CUSTOM_FORMAT else FORMATS[self.format]

    def slot(self, name: str) -> ModuleSpec:
        return getattr(self, name)

    # --- serialización -------------------------------------------------------------

    def to_dict(self, full=False) -> dict:
        """Dict listo para JSON. Con ``full=True`` las opciones incluyen los valores por defecto."""
        d = {
            "version": self.version, "format": self.format,
            "size_mm": list(self.size_mm) if self.size_mm else None,
            "dpi": self.dpi, "seed": self.seed,
            "palette": _flat(self.palette), "style": _flat(self.style), "symmetry": _flat(self.symmetry),
        }
        for name in SLOTS:
            spec = self.slot(name)
            options = copy.deepcopy(spec.options)
            if full and spec.kind != NO_MODULE:
                from .registry import get_module
                options = get_module(name, spec.kind).resolve_options(options)
            d[name] = {"kind": spec.kind, "enabled": spec.enabled, "options": options}
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DorsoConfig":
        data = merge(DorsoConfig().to_dict(), data)
        _check_keys(data, {"version", "format", "size_mm", "dpi", "seed", "palette", "style", "symmetry", *SLOTS}, "")
        if data["version"] != CONFIG_VERSION:
            raise ConfigError(f"versión de configuración no soportada: {data['version']}")
        cfg = cls(
            version=data["version"], format=data["format"],
            size_mm=tuple(data["size_mm"]) if data["size_mm"] else None,
            dpi=data["dpi"], seed=data["seed"],
            palette=_build(Palette, data["palette"], "palette"),
            style=_build(Style, data["style"], "style"),
            symmetry=_build(Symmetry, data["symmetry"], "symmetry"),
            **{name: _build_spec(data[name], name) for name in SLOTS},
        )
        cfg.validate()
        return cfg

    def to_json(self, full=False) -> str:
        return json.dumps(self.to_dict(full), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "DorsoConfig":
        return cls.from_dict(json.loads(text))

    def save(self, path) -> None:
        Path(path).write_text(self.to_json(full=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path) -> "DorsoConfig":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    # --- validación ----------------------------------------------------------------

    def validate(self) -> None:
        if self.format == CUSTOM_FORMAT:
            if not self.size_mm or len(self.size_mm) != 2:
                raise ConfigError("format=custom requiere size_mm=[ancho, alto]")
            if not all(isinstance(v, (int, float)) and MIN_SIZE_MM <= v <= MAX_SIZE_MM for v in self.size_mm):
                raise ConfigError(f"size_mm fuera de [{MIN_SIZE_MM}, {MAX_SIZE_MM}] mm")
        elif self.format not in FORMATS:
            raise ConfigError(f"format desconocido {self.format!r}; válidos: {[*FORMATS, CUSTOM_FORMAT]}")
        if not isinstance(self.dpi, int) or not MIN_DPI <= self.dpi <= MAX_DPI:
            raise ConfigError(f"dpi debe ser un entero en [{MIN_DPI}, {MAX_DPI}]")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ConfigError("seed debe ser un entero")
        for role in Palette.__dataclass_fields__:
            Opt("#000000", color=True).check(f"palette.{role}", getattr(self.palette, role))
        for name, (lo, hi) in STYLE_LIMITS.items():
            value = getattr(self.style, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
                raise ConfigError(f"style.{name}={value!r} fuera de [{lo}, {hi}]")
        for name in ("bilateral", "rotational_180"):
            if not isinstance(getattr(self.symmetry, name), bool):
                raise ConfigError(f"symmetry.{name} debe ser true/false")
        from .registry import get_module
        for name in SLOTS:
            spec = self.slot(name)
            if not isinstance(spec.enabled, bool) or not isinstance(spec.options, dict):
                raise ConfigError(f"{name}: 'enabled' debe ser booleano y 'options' un objeto")
            if spec.kind != NO_MODULE:
                try:
                    cls = get_module(name, spec.kind)
                except KeyError as e:
                    raise ConfigError(str(e.args[0])) from None
                cls.resolve_options(spec.options)


# --- utilidades de dicts ---------------------------------------------------------------

def merge(base: dict, override: dict) -> dict:
    """Mezcla profunda: los dicts se fusionan, todo lo demás se reemplaza."""
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and k != "options":
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def get_path(d: dict, path: str):
    for key in path.split("."):
        d = d[key]
    return d


def set_path(d: dict, path: str, value) -> None:
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def _flat(obj) -> dict:
    return {f.name: getattr(obj, f.name) for f in fields(obj)}


def _check_keys(data: dict, allowed: set, where: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ConfigError(f"claves desconocidas en {where or 'la raíz'}: {sorted(unknown)}")


def _build(cls, data: dict, where: str):
    _check_keys(data, {f.name for f in fields(cls)}, where)
    return cls(**data)


def _build_spec(data: dict, where: str) -> ModuleSpec:
    if not isinstance(data, dict):
        raise ConfigError(f"{where}: se esperaba un objeto con kind/enabled/options")
    return _build(ModuleSpec, data, where)
