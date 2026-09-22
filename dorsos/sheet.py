"""Hoja de muestras: cuadrícula de dorsos con su etiqueta, y catálogo de variantes por ranura."""
from PIL import Image, ImageDraw, ImageFont

from .compose import build_scene
from .config import DorsoConfig
from .constants import MM_PER_INCH
from .render_png import render_png
from .registry import get_module, kinds

# Fondo neutro sobre el que se enseña cada ranura en el catálogo.
CATALOG_BASE = {
    "frame": {"pattern": {"kind": "celosia"}},
    "pattern": {"frame": {"kind": "doble"}},
    "medallion": {"frame": {"kind": "doble"}, "pattern": {"kind": "reticula", "options": {"style": "lineas"}}},
    "corners": {"frame": {"kind": "doble"}, "pattern": {"kind": "reticula", "options": {"style": "lineas"}}},
}
# Opción que distingue las variantes de un módulo, si la tiene.
VARIANT_OPTIONS = ("style", "motif")

BACKGROUND = (214, 214, 218)
LABEL_COLOR = (40, 40, 48)
GAP_PX = 18
LABEL_PX = 26


def contact_sheet(items, cols: int, card_height_px: int = 420) -> Image.Image:
    """``items``: lista de ``(etiqueta, DorsoConfig)``. Cada carta se escala a ``card_height_px`` de alto."""
    font = ImageFont.load_default(size=13)
    cards = []
    for label, cfg in items:
        scene = build_scene(cfg)
        dpi = max(30, round(card_height_px / (scene.height / MM_PER_INCH)))
        cards.append((label, render_png(scene, dpi)))
    cell_w = max(img.width for _, img in cards)
    cell_h = max(img.height for _, img in cards) + LABEL_PX
    rows = -(-len(cards) // cols)
    sheet = Image.new("RGB", (GAP_PX + cols * (cell_w + GAP_PX), GAP_PX + rows * (cell_h + GAP_PX)), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for n, (label, img) in enumerate(cards):
        x = GAP_PX + (n % cols) * (cell_w + GAP_PX)
        y = GAP_PX + (n // cols) * (cell_h + GAP_PX)
        sheet.paste(img, (x + (cell_w - img.width) // 2, y), img)
        draw.text((x + cell_w / 2, y + img.height + 4), label, fill=LABEL_COLOR, font=font, anchor="ma")
    return sheet


def catalog(slot: str) -> list[tuple[str, DorsoConfig]]:
    """Una carta por cada módulo de ``slot`` y por cada valor de su opción de variante.

    Los módulos declaran en ``mirror_free`` las variantes que solo tienen simetría de giro
    (una espiral): se enseñan sin el espejo, que las convertiría en otra cosa.
    """
    items = []
    for kind in kinds(slot):
        cls = get_module(slot, kind)
        key = next((k for k in VARIANT_OPTIONS if k in cls.options), None)
        for value in cls.options[key].choices if key else (None,):
            data = {**CATALOG_BASE[slot], slot: {"kind": kind, "options": {key: value} if key else {}}}
            if value in getattr(cls, "mirror_free", ()):
                data["symmetry"] = {"bilateral": False, "rotational_180": True}
            items.append((f"{kind} / {value}" if key else kind, DorsoConfig.from_dict(data)))
    return items
