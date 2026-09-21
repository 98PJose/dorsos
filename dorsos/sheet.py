"""Hoja de muestras: cuadrícula de dorsos con su etiqueta."""
from PIL import Image, ImageDraw, ImageFont

from .compose import build_scene
from .constants import MM_PER_INCH
from .render_png import render_png

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
