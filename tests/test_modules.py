import pytest

from dorsos import DorsoConfig, build_scene, render_png, render_svg
from dorsos.constants import SLOTS
from dorsos.registry import get_module, kinds


def scene_for(slot, kind, options=None):
    return build_scene(DorsoConfig.from_dict({slot: {"kind": kind, "options": options or {}}}))


@pytest.mark.parametrize("slot,kind", [(s, k) for s in SLOTS for k in kinds(s)])
def test_every_module_renders(slot, kind):
    scene = scene_for(slot, kind)
    render_png(scene, 30, supersample=2)
    render_svg(scene)


def single_option_cases():
    for slot in SLOTS:
        for kind in kinds(slot):
            for key, opt in get_module(slot, kind).options.items():
                if opt.choices:
                    for value in opt.choices:
                        yield slot, kind, key, value
                elif opt.lo is not None:
                    yield slot, kind, key, opt.lo
                    yield slot, kind, key, opt.hi


@pytest.mark.parametrize("slot,kind,key,value", list(single_option_cases()))
def test_every_option_value_builds(slot, kind, key, value):
    scene = scene_for(slot, kind, {key: value})
    render_png(scene, 20, supersample=2)


def test_registry_covers_requested_features():
    assert set(kinds("frame")) >= {"simple", "doble", "geometrico", "ornamentado"}
    assert set(kinds("pattern")) >= {"rombos", "reticula", "rosetas", "ondas", "arabescos", "guilloche"}
    assert set(kinds("medallion")) >= {"circulo", "rombo", "roseta"}
    assert kinds("corners")


def test_custom_module_can_be_registered():
    from dorsos.modules.base import Module, Opt
    from dorsos.primitives import circle
    from dorsos.registry import _REGISTRY, register

    @register("medallion", "punto_de_prueba")
    class Dot(Module):
        options = {"r": Opt(2.0, lo=0.5, hi=9.0)}

        def build(self, ctx):
            return [circle(ctx.field.cx, ctx.field.cy, self.o["r"], fill="#000000")]

    try:
        cfg = DorsoConfig.from_dict({"medallion": {"kind": "punto_de_prueba", "options": {"r": 3}}})
        assert build_scene(cfg).layers[-1].items[0].r == 3
    finally:
        del _REGISTRY["medallion"]["punto_de_prueba"]


def test_diagonal_lattice_is_symmetric_by_itself():
    """La celosía ancla sus rectas en el centro, sin apoyarse en la simetría global.

    Se compara la geometría y no los píxeles: el trazo grueso de Pillow no es simétrico
    al píxel, y eso solo lo arregla el espejo del dominio fundamental.
    """
    import math

    from dorsos.geometry import Affine

    cfg = DorsoConfig.from_dict({"pattern": {"kind": "celosia"}, "frame": {"kind": "none"},
                                 "symmetry": {"bilateral": False, "rotational_180": False}})
    scene = build_scene(cfg)
    segments = scene.layers[2].items

    def canonical(prim, aff=None):
        pts = [aff(p) for p in prim.points] if aff else prim.points
        return tuple(sorted((round(x, 6), round(y, 6)) for x, y in pts))

    original = {canonical(p) for p in segments}
    assert len(original) > 10
    for aff in (Affine.mirror_x(scene.width / 2), Affine.rotate(math.pi, scene.width / 2, scene.height / 2)):
        assert {canonical(p, aff) for p in segments} == original


def test_bleed_lets_the_pattern_reach_the_field_edge():
    def clip_width(bleed):
        cfg = DorsoConfig.from_dict({"pattern": {"kind": "celosia"},
                                     "frame": {"kind": "doble", "options": {"bleed": bleed}}})
        clip = build_scene(cfg).layers[2].clip
        return max(x for x, _ in clip) - min(x for x, _ in clip)

    assert clip_width(True) > clip_width(False)


@pytest.mark.parametrize("kind,style", [("panal", "simple"), ("damasco", "ojiva"), ("sembrado", "cruz")])
def test_staggered_lattice_is_symmetric_by_itself(kind, style):
    """Las filas al tresbolillo se anclan en el centro, sin apoyarse en la simetría global."""
    import math

    from dorsos.geometry import Affine

    cfg = DorsoConfig.from_dict({"pattern": {"kind": kind, "options": {"style": style}},
                                 "frame": {"kind": "none"},
                                 "symmetry": {"bilateral": False, "rotational_180": False}})
    scene = build_scene(cfg)
    card = (0, 0, scene.width, scene.height)

    def inside(prim):
        """Solo lo visible: las celdas de relleno de fuera de la carta las quita el recorte."""
        return all(card[0] <= x <= card[2] and card[1] <= y <= card[3] for x, y in prim.points)

    shapes = [p for p in scene.layers[2].items if hasattr(p, "points") and inside(p)]

    def canonical(prim, aff=None):
        pts = [aff(p) for p in prim.points] if aff else prim.points
        return tuple(sorted((round(x, 5), round(y, 5)) for x, y in pts))

    original = {canonical(p) for p in shapes}
    assert len(original) > 10
    for aff in (Affine.mirror_x(scene.width / 2), Affine.rotate(math.pi, scene.width / 2, scene.height / 2)):
        assert {canonical(p, aff) for p in shapes} == original


def test_braid_redraws_half_the_crossings():
    """La trenza necesita los parches: sin ellos no hay efecto de encima y debajo."""
    cfg = DorsoConfig.from_dict({"pattern": {"kind": "entrelazo", "options": {"style": "trenza"}}})
    plain = DorsoConfig.from_dict({"pattern": {"kind": "celosia"}})
    assert len(build_scene(cfg).layers[2].items) > len(build_scene(plain).layers[2].items)
