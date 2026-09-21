"""Renderizador raster (Pillow): dibuja a SUPERSAMPLE x, aplica la simetría y reduce."""
from PIL import Image, ImageChops, ImageDraw
from PIL.PngImagePlugin import PngInfo

from .constants import MM_PER_INCH, SUPERSAMPLE
from .primitives import Circle, Polygon, Polyline
from .scene import Scene

METADATA_KEY = "dorsos.config"


def pixel_size(scene: Scene, dpi: int) -> tuple[int, int]:
    """Tamaño final en píxeles para que ``px / dpi`` reproduzca el tamaño físico."""
    return round(scene.width / MM_PER_INCH * dpi), round(scene.height / MM_PER_INCH * dpi)


def render_png(scene: Scene, dpi: int, supersample: int = SUPERSAMPLE) -> Image.Image:
    if supersample % 2:
        raise ValueError("supersample debe ser par para que la simetría caiga entre píxeles")
    pw, ph = pixel_size(scene, dpi)
    size = (pw * supersample, ph * supersample)
    # Escala por eje: el centro de la carta coincide con el del lienzo aunque el redondeo
    # a píxeles enteros altere la escala en menos de un 0,1 %.
    kx, ky = size[0] / scene.width, size[1] / scene.height
    first_paper = _first_fill(scene) or "#ffffff"
    img = Image.new("RGBA", size, _rgb(first_paper) + (0,))  # sin alfa: el borde no se oscurece al reducir
    for group in scene.layers:
        _draw_group(img, group, kx, ky)
    _apply_symmetry(img, scene)
    return img.reduce(supersample)


def save_png(img: Image.Image, path, dpi: int, metadata: str = "") -> None:
    info = PngInfo()
    if metadata:
        info.add_text(METADATA_KEY, metadata)
    img.save(path, dpi=(dpi, dpi), pnginfo=info, optimize=True)


def _first_fill(scene):
    for group in scene.layers:
        for p in group.items:
            if isinstance(p, Polygon) and p.fill:
                return p.fill
    return None


def _rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _draw_group(img, group, kx, ky):
    if group.clip is None:
        _draw_items(ImageDraw.Draw(img), group.items, kx, ky)
        return
    outside = img.copy()
    _draw_items(ImageDraw.Draw(img), group.items, kx, ky)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(_px(group.clip, kx, ky), fill=255)
    img.paste(outside, mask=ImageChops.invert(mask))


def _px(points, kx, ky):
    return [(x * kx, y * ky) for x, y in points]


def _draw_items(draw, items, kx, ky):
    k = (kx + ky) / 2
    for p in items:
        if isinstance(p, Circle):
            _draw_circle(draw, p, kx, ky, k)
        elif isinstance(p, Polygon):
            pts = _px(p.points, kx, ky)
            if p.fill:
                draw.polygon(pts, fill=p.fill)
            if p.stroke and p.width > 0:
                _stroke(draw, pts + pts[:2], p.stroke, p.width * k, caps=False)
        elif isinstance(p, Polyline):
            _stroke(draw, _px(p.points, kx, ky), p.stroke, p.width * k, caps=True)


def _draw_circle(draw, c, kx, ky, k):
    cx, cy = c.cx * kx, c.cy * ky
    if c.fill:
        draw.ellipse((cx - c.r * kx, cy - c.r * ky, cx + c.r * kx, cy + c.r * ky), fill=c.fill)
    if c.stroke and c.width > 0:
        w = max(1, round(c.width * k))
        half = c.width * k / 2  # el trazo SVG va centrado en la circunferencia; el de Pillow, hacia dentro
        draw.ellipse((cx - c.r * kx - half, cy - c.r * ky - half, cx + c.r * kx + half, cy + c.r * ky + half),
                     outline=c.stroke, width=w)


def _stroke(draw, pts, color, width_px, caps):
    w = max(1, round(width_px))
    draw.line(pts, fill=color, width=w, joint="curve")
    if caps and w >= 3:
        r = w / 2
        for x, y in (pts[0], pts[-1]):
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _apply_symmetry(img, scene):
    if not (scene.bilateral or scene.rotational_180):
        return
    w, h = img.size
    w2, h2 = w // 2, h // 2
    flip_h, flip_v, rot = Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.FLIP_TOP_BOTTOM, Image.Transpose.ROTATE_180
    if scene.bilateral and scene.rotational_180:
        q = img.crop((0, 0, w2, h2))
        img.paste(q.transpose(flip_h), (w2, 0))
        img.paste(q.transpose(rot), (w2, h2))
        img.paste(q.transpose(flip_v), (0, h2))
    elif scene.bilateral:
        img.paste(img.crop((0, 0, w2, h)).transpose(flip_h), (w2, 0))
    else:
        img.paste(img.crop((0, 0, w, h2)).transpose(rot), (0, h2))
