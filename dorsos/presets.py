"""Presets: configuraciones parciales en ``dorsos/presets/*.json`` que se mezclan sobre los valores por defecto."""
import json
from pathlib import Path

from .errors import ConfigError

PRESET_DIR = Path(__file__).with_name("presets")


def preset_names() -> list[str]:
    return sorted(p.stem for p in PRESET_DIR.glob("*.json"))


def load_preset(name: str) -> dict:
    path = PRESET_DIR / f"{name}.json"
    if not path.is_file():
        raise ConfigError(f"preset desconocido {name!r}; disponibles: {', '.join(preset_names())}")
    return json.loads(path.read_text(encoding="utf-8"))
