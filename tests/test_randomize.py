import pytest

from dorsos import DorsoConfig
from dorsos.errors import ConfigError
from dorsos.randomize import randomize


def test_same_seed_same_design():
    base = DorsoConfig()
    assert randomize(base, 5).to_dict() == randomize(base, 5).to_dict()
    assert randomize(base, 5).to_dict() != randomize(base, 6).to_dict()


def test_format_dpi_and_symmetry_are_not_randomized():
    base = DorsoConfig.from_dict({"format": "espanola", "dpi": 150,
                                  "symmetry": {"bilateral": True, "rotational_180": False}})
    for seed in range(20):
        cfg = randomize(base, seed)
        assert (cfg.format, cfg.dpi, cfg.symmetry) == (base.format, 150, base.symmetry)


def test_locked_blocks_survive():
    base = DorsoConfig.from_dict({"palette": {"background": "#123456"},
                                  "frame": {"kind": "geometrico", "options": {"motif": "puntos"}}})
    for seed in range(30):
        cfg = randomize(base, seed, lock=["palette", "frame"])
        assert cfg.palette == base.palette
        assert cfg.frame.kind == "geometrico" and cfg.frame.options["motif"] == "puntos"


def test_lock_single_field_and_option():
    base = DorsoConfig.from_dict({"palette": {"background": "#123456"},
                                  "pattern": {"kind": "rombos", "options": {"style": "cruzado"}}})
    for seed in range(30):
        cfg = randomize(base, seed, lock=["palette.background", "pattern.kind", "pattern.options.style"])
        assert cfg.palette.background == "#123456"
        assert cfg.pattern.kind == "rombos" and cfg.pattern.options["style"] == "cruzado"


def test_locked_kind_still_randomizes_its_options():
    base = DorsoConfig.from_dict({"pattern": {"kind": "rosetas"}})
    styles = {randomize(base, s, lock=["pattern.kind"]).pattern.options["style"] for s in range(40)}
    assert len(styles) > 1


def test_unknown_lock_path_is_an_error():
    with pytest.raises(ConfigError):
        randomize(DorsoConfig(), 1, lock=["palette.nada"])


def test_random_configs_are_valid_and_serializable():
    base = DorsoConfig()
    for seed in range(100):
        cfg = randomize(base, seed)
        assert DorsoConfig.from_json(cfg.to_json(full=True)).to_dict(full=True) == cfg.to_dict(full=True)


def test_layers_randomize_only_the_chosen_ones():
    base = DorsoConfig.from_dict({"palette": {"background": "#123456"}, "frame": {"kind": "ornamentado"},
                                  "pattern": {"kind": "rombos"}, "medallion": {"kind": "rombo"}})
    patterns = set()
    for seed in range(40):
        cfg = randomize(base, seed, layers=["pattern"])
        assert cfg.palette == base.palette
        assert cfg.frame.kind == "ornamentado" and cfg.medallion.kind == "rombo"
        assert cfg.style == base.style
        patterns.add(cfg.pattern.kind)
    assert len(patterns) > 1


def test_several_layers_at_once():
    base = DorsoConfig.from_dict({"frame": {"kind": "ornamentado"}, "corners": {"kind": "abanico"}})
    for seed in range(20):
        cfg = randomize(base, seed, layers=["palette", "pattern", "medallion"])
        assert cfg.frame.kind == "ornamentado" and cfg.corners.kind == "abanico"


def test_no_layers_given_randomizes_everything():
    base = DorsoConfig.from_dict({"frame": {"kind": "ornamentado"}})
    frames = {randomize(base, s).frame.kind for s in range(40)}
    assert len(frames) > 1


def test_unknown_layer_is_an_error():
    with pytest.raises(ConfigError):
        randomize(DorsoConfig(), 1, layers=["patron"])


def test_lock_still_applies_inside_a_randomized_layer():
    base = DorsoConfig.from_dict({"pattern": {"kind": "celosia"}})
    for seed in range(20):
        cfg = randomize(base, seed, lock=["pattern.kind"], layers=["pattern"])
        assert cfg.pattern.kind == "celosia"
