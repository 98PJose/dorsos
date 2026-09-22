import pytest

from dorsos import DorsoConfig, build_scene
from dorsos.modules.keys import KEYS, fitted_spiral, spiral_paths
from dorsos.registry import get_module
from dorsos.sheet import catalog


def segment_boxes(path):
    """Rectángulo de cada tramo, en unidades: el trazo mide una unidad de grueso."""
    return [(min(ax, bx) - 0.5, min(ay, by) - 0.5, max(ax, bx) + 0.5, max(ay, by) + 0.5)
            for (ax, ay), (bx, by) in zip(path, path[1:])]


def gap(a, b):
    """Separación entre dos rectángulos; negativa si se solapan."""
    return max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])


def assert_strokes_keep_their_gap(path):
    """Trazo y hueco miden lo mismo: dos tramos no contiguos quedan a una unidad o más."""
    boxes = segment_boxes(path)
    for i, a in enumerate(boxes):
        for j in range(i + 2, len(boxes)):
            assert gap(a, boxes[j]) >= 1 - 1e-9, (i, j, a, boxes[j])


@pytest.mark.parametrize("name", list(KEYS))
def test_key_modules_chain_into_one_line(name):
    key = KEYS[name]
    (x0, y0), (x1, y1) = key.path[0], key.path[-1]
    assert (x1, y1) == (x0 + key.period, y0)


@pytest.mark.parametrize("name", list(KEYS))
def test_key_keeps_stroke_and_gap_equal_across_modules(name):
    key = KEYS[name]
    two_modules = list(key.path) + [(x + key.period, y) for x, y in key.path[1:]]
    assert_strokes_keep_their_gap(two_modules)


def test_meandro_matches_the_reference_grid():
    """La greca de referencia: módulo de 10 × 9 y banda de 13 con raíles."""
    key = KEYS["meandro"]
    assert (key.period, key.height, key.band_units) == (10, 9, 13)


@pytest.mark.parametrize("half", [(10, 14), (20.5, 29.5), (40.2, 58.1), (60, 90)])
def test_spiral_is_one_continuous_line_that_never_touches_itself(half):
    X, Y = fitted_spiral(*half)
    paths = spiral_paths(X, Y)
    assert len(paths) == 1
    assert_strokes_keep_their_gap(paths[0])


def test_spiral_is_symmetric_under_half_turn():
    X, Y = fitted_spiral(30.3, 44.7)
    boxes = {tuple(round(v, 6) for v in b) for b in segment_boxes(spiral_paths(X, Y)[0])}
    turned = {tuple(round(v, 6) for v in (-b[2], -b[3], -b[0], -b[1])) for b in boxes}
    assert boxes == turned


def test_greca_border_uses_an_even_number_of_modules():
    """El centro de cada lado cae entre dos módulos, así el espejo no parte ninguno."""
    frame = get_module("frame", "geometrico")({"motif": "greca", "band_mm": 5.0})
    for length in (40.0, 51.3, 57.0, 72.9, 83.4):
        assert frame.unit_count(length, 5.0) % 2 == 0


def test_band_corners_are_reflected_not_translated():
    """Sin simetría global, la esquina de abajo a la derecha es la de arriba girada."""
    cfg = DorsoConfig.from_dict({"frame": {"kind": "geometrico", "options": {"motif": "greca"}},
                                 "pattern": {"kind": "none"},
                                 "symmetry": {"bilateral": False, "rotational_180": False}})
    scene = build_scene(cfg)
    w, h = scene.width, scene.height
    shapes = [p for p in scene.layers[-1].items if hasattr(p, "points")]
    near = lambda p, x, y: all(abs(px - x) < 8 and abs(py - y) < 8 for px, py in p.points)  # noqa: E731
    top_left = {tuple(sorted((round(x, 4), round(y, 4)) for x, y in p.points)) for p in shapes if near(p, 3, 3)}
    bottom_right = {tuple(sorted((round(w - x, 4), round(h - y, 4)) for x, y in p.points))
                    for p in shapes if near(p, w - 3, h - 3)}
    assert top_left and top_left == bottom_right


def test_catalog_shows_mirror_free_variants_without_the_mirror():
    for label, cfg in catalog("pattern"):
        assert cfg.symmetry.bilateral == (label != "greca / espiral")
