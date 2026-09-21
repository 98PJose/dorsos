import xml.dom.minidom

import pytest
from PIL import Image, ImageChops

from dorsos import DorsoConfig, build_scene, render_png, render_svg, save_png
from dorsos.render_png import pixel_size

LOW_DPI = 40
FULL = {"pattern": {"kind": "rosetas", "options": {"variation": 0.5}}, "medallion": {"kind": "circulo"},
        "corners": {"kind": "abanico"}}


def render(overrides=None, dpi=LOW_DPI):
    cfg = DorsoConfig.from_dict({**FULL, **(overrides or {})})
    return render_png(build_scene(cfg), dpi, supersample=2)


@pytest.mark.parametrize("fmt,size_mm", [("poker", (63.0, 88.0)), ("espanola", (61.5, 95.0))])
def test_png_has_physical_size(tmp_path, fmt, size_mm):
    cfg = DorsoConfig.from_dict({"format": fmt, "dpi": 300})
    scene = build_scene(cfg)
    path = tmp_path / "a.png"
    save_png(render_png(scene, 300), path, 300, scene.metadata)
    img = Image.open(path)
    dpi = img.info["dpi"][0]
    assert dpi == pytest.approx(300, abs=0.01)
    for px, mm in zip(img.size, size_mm):
        assert px / dpi * 25.4 == pytest.approx(mm, abs=0.05)
    assert "dorsos.config" in img.text  # la configuración viaja dentro del PNG


def test_resolution_is_configurable():
    scene = build_scene(DorsoConfig())
    w300, h300 = pixel_size(scene, 300)
    w600, h600 = pixel_size(scene, 600)
    assert w600 == pytest.approx(2 * w300, abs=1) and h600 == pytest.approx(2 * h300, abs=1)


def test_same_seed_same_pixels():
    assert ImageChops.difference(render({"seed": 4}), render({"seed": 4})).getbbox(alpha_only=False) is None


def test_seed_changes_seeded_variation():
    assert ImageChops.difference(render({"seed": 4}), render({"seed": 5})).getbbox(alpha_only=False) is not None


@pytest.mark.parametrize("sym", [
    {"bilateral": True, "rotational_180": False},
    {"bilateral": False, "rotational_180": True},
    {"bilateral": True, "rotational_180": True},
])
def test_symmetry_is_pixel_exact(sym):
    img = render({"symmetry": sym}).convert("RGBA")
    flips = []
    if sym["bilateral"]:
        flips.append(Image.Transpose.FLIP_LEFT_RIGHT)
    if sym["rotational_180"]:
        flips.append(Image.Transpose.ROTATE_180)
    if sym["bilateral"] and sym["rotational_180"]:
        flips.append(Image.Transpose.FLIP_TOP_BOTTOM)
    for t in flips:
        assert ImageChops.difference(img, img.transpose(t)).getbbox(alpha_only=False) is None


def test_without_symmetry_random_variation_is_asymmetric():
    img = render({"symmetry": {"bilateral": False, "rotational_180": False}}).convert("RGBA")
    assert ImageChops.difference(img, img.transpose(Image.Transpose.ROTATE_180)).getbbox(alpha_only=False) is not None


def test_toggling_a_module_leaves_the_others_untouched():
    with_medallion = build_scene(DorsoConfig.from_dict(FULL))
    without = build_scene(DorsoConfig.from_dict({**FULL, "medallion": {"kind": "circulo", "enabled": False}}))
    pattern_layer = 2  # capas: papel, campo, patrón, marco, medallón, esquinas
    assert with_medallion.layers[pattern_layer].items == without.layers[pattern_layer].items
    assert len(without.layers) == len(with_medallion.layers) - 1


def test_disabled_and_none_are_equivalent():
    a = build_scene(DorsoConfig.from_dict({"medallion": {"kind": "circulo", "enabled": False}}))
    b = build_scene(DorsoConfig.from_dict({"medallion": {"kind": "none"}}))
    assert len(a.layers) == len(b.layers)


def test_transparent_corners_and_opaque_center():
    img = render({"style": {"corner_radius_mm": 4.0}})
    assert img.getpixel((0, 0))[3] == 0
    assert img.getpixel((img.width // 2, img.height // 2))[3] == 255


def test_svg_is_valid_xml_with_physical_size():
    scene = build_scene(DorsoConfig.from_dict({**FULL, "format": "espanola"}))
    doc = xml.dom.minidom.parseString(render_svg(scene))
    root = doc.documentElement
    assert root.getAttribute("width") == "61.5mm" and root.getAttribute("height") == "95mm"
    assert root.getAttribute("viewBox") == "0 0 61.5 95"
    assert len(doc.getElementsByTagName("use")) == 4  # dorso base + 3 isometrías del grupo


def test_svg_without_symmetry_has_no_clones():
    cfg = DorsoConfig.from_dict({"symmetry": {"bilateral": False, "rotational_180": False}})
    assert "<use" not in render_svg(build_scene(cfg))
