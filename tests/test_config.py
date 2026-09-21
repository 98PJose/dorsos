import pytest

from dorsos import DorsoConfig
from dorsos.errors import ConfigError
from dorsos.presets import load_preset, preset_names


def test_json_roundtrip_is_lossless():
    cfg = DorsoConfig.from_dict({"pattern": {"kind": "rosetas", "options": {"style": "mosaico"}},
                                 "medallion": {"kind": "estrella"}, "seed": 9})
    again = DorsoConfig.from_json(cfg.to_json(full=True))
    assert again.to_dict(full=True) == cfg.to_dict(full=True)


def test_partial_dict_uses_defaults():
    cfg = DorsoConfig.from_dict({"format": "espanola"})
    assert cfg.size == (61.5, 95.0) and cfg.dpi == 300 and cfg.symmetry.bilateral


@pytest.mark.parametrize("bad", [
    {"palete": {}},                                             # clave raíz desconocida
    {"palette": {"fondo": "#fff"}},                             # clave de paleta desconocida
    {"palette": {"background": "rojo"}},                        # color inválido
    {"style": {"density": 2.0}},                                # fuera de rango
    {"dpi": 5},
    {"format": "tarot"},
    {"frame": {"kind": "inexistente"}},
    {"pattern": {"kind": "rombos", "options": {"style": "x"}}},  # opción fuera de las permitidas
    {"pattern": {"kind": "rombos", "options": {"nope": 1}}},     # opción desconocida
    {"symmetry": {"bilateral": "si"}},
    {"format": "custom"},                                       # falta size_mm
])
def test_invalid_config_is_rejected(bad):
    with pytest.raises(ConfigError):
        DorsoConfig.from_dict(bad)


def test_custom_size():
    assert DorsoConfig.from_dict({"format": "custom", "size_mm": [50, 70]}).size == (50, 70)


def test_every_preset_is_valid_json_and_config():
    assert len(preset_names()) >= 6
    for name in preset_names():
        DorsoConfig.from_dict(load_preset(name))


def test_unknown_preset():
    with pytest.raises(ConfigError):
        load_preset("no-existe")
