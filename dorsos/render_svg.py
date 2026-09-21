"""Renderizador SVG: mismas primitivas, unidades en mm (el SVG mide lo mismo que la carta)."""
from xml.sax.saxutils import escape

from .primitives import Circle, Polygon
from .scene import Scene


def _n(x: float) -> str:
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pts(points) -> str:
    return " ".join(f"{_n(x)},{_n(y)}" for x, y in points)


def _prim(p) -> str:
    if isinstance(p, Circle):
        attrs = f'cx="{_n(p.cx)}" cy="{_n(p.cy)}" r="{_n(p.r)}"'
        return f"<circle {attrs}{_paint(p.fill, p.stroke, p.width)}/>"
    if isinstance(p, Polygon):
        return f'<polygon points="{_pts(p.points)}"{_paint(p.fill, p.stroke, p.width)}/>'
    return f'<polyline points="{_pts(p.points)}"{_paint(None, p.stroke, p.width)}/>'


def _paint(fill, stroke, width) -> str:
    out = f' fill="{fill}"' if fill else ' fill="none"'
    if stroke and width > 0:
        out += f' stroke="{stroke}" stroke-width="{_n(width)}"'
    return out


def render_svg(scene: Scene) -> str:
    w, h = scene.width, scene.height
    defs, body, clip_id = [], [], 0

    for group in scene.layers:
        items = "".join(_prim(p) for p in group.items)
        if group.clip is None:
            body.append(items)
        else:
            clip_id += 1
            defs.append(f'<clipPath id="c{clip_id}"><polygon points="{_pts(group.clip)}"/></clipPath>')
            body.append(f'<g clip-path="url(#c{clip_id})">{items}</g>')

    # Carta completa dentro de un <g>: el dominio se recorta y se replica con <use>.
    content = "".join(body)
    if scene.bilateral or scene.rotational_180:
        _, plan = scene.symmetry_plan()
        defs.append(f'<g id="dorso">{content}</g>')
        # La carta sin recortar va debajo: así la costura entre dominios (que el antialiasing
        # aclararía) se mezcla con contenido casi idéntico en lugar de con el fondo.
        shown = ['<use href="#dorso"/>']
        for i, (aff, target) in enumerate(plan):
            defs.append(f'<clipPath id="t{i}"><rect x="{_n(target.x0)}" y="{_n(target.y0)}" '
                        f'width="{_n(target.w)}" height="{_n(target.h)}"/></clipPath>')
            matrix = f"matrix({_n(aff.a)} {_n(aff.c)} {_n(aff.b)} {_n(aff.d)} {_n(aff.e)} {_n(aff.f)})"
            shown.append(f'<g clip-path="url(#t{i})"><use href="#dorso" transform="{matrix}"/></g>')
        content = "".join(shown)

    meta = f"<desc>{escape(scene.metadata)}</desc>" if scene.metadata else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}mm" height="{_n(h)}mm" '
            f'viewBox="0 0 {_n(w)} {_n(h)}" stroke-linecap="round" stroke-linejoin="round">'
            f'{meta}<defs>{"".join(defs)}</defs>{content}</svg>\n')
