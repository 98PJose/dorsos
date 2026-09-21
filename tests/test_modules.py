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
