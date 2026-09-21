"""Marcos: simple, doble, geométrico y ornamentado.

Un marco recibe el campo interior al margen de papel y devuelve sus primitivas más la
zona interior libre (``FrameResult``). Los marcos con banda dibujan un motivo repetido
en los cuatro lados; el motivo se define en coordenadas locales ``(u, v)`` con ``u``
a lo largo del lado y ``v`` desde el borde exterior (0) al interior (``t``).
"""
import math

from ..geometry import Affine, Rect, lens, rect_outline
from ..primitives import circle, line, poly, transform_all
from ..registry import register
from .base import FrameResult, Module, Opt
from .motifs import rosette

CORNERS = ("recto", "redondo", "cortado", "concavo")
FIELD_RADIUS_MM = 0.8  # el campo de color siempre lleva un redondeo leve


class Frame(Module):
    def field_outline(self, rect):
        return rect_outline(rect, "redondo", FIELD_RADIUS_MM)

    def build(self, ctx) -> FrameResult:
        raise NotImplementedError


class LineFrame(Frame):
    """Marcos de línea: una o dos líneas concéntricas con esquina configurable."""
    def build(self, ctx):
        o = self.o
        color = ctx.color(o["color"])
        base = ctx.field.inset(o["inset_mm"])
        prims = []
        for weight, offset in self.line_specs(o):
            rect = base.inset(offset)
            prims.append(poly(rect_outline(rect, o["corner"], self.radius_at(o, offset)),
                              stroke=color, width=ctx.weight(weight)))
        last = self.line_specs(o)[-1][1]
        inner = base.inset(last + o["pad_mm"])
        inner_pts = rect_outline(inner, o["corner"], self.radius_at(o, last + o["pad_mm"]))
        return FrameResult(prims, self.field_outline(ctx.field), inner_pts, inner)

    @staticmethod
    def radius_at(o, offset):
        """Los redondeos y chaflanes se encogen hacia dentro; los cóncavos mantienen su tamaño."""
        return o["radius_mm"] if o["corner"] == "concavo" else max(o["radius_mm"] - offset, 0.4)

    def line_specs(self, o):
        """Lista de ``(peso, distancia al rectángulo base)`` por línea."""
        raise NotImplementedError


_LINE_OPTIONS = {
    "color": Opt("primary", "color de las líneas", color=True, rand=False),
    "inset_mm": Opt(1.0, "distancia del campo al marco", lo=0.0, hi=4.0),
    "pad_mm": Opt(0.9, "aire entre el marco y el interior", lo=0.0, hi=4.0),
    "corner": Opt("redondo", "forma de las esquinas", choices=CORNERS),
    "radius_mm": Opt(2.4, "tamaño de la esquina", lo=0.5, hi=6.0, rlo=1.5, rhi=3.5),
}


@register("frame", "simple")
class SimpleFrame(LineFrame):
    doc = "Una línea con esquinas rectas, redondas, cortadas o cóncavas."
    options = {**_LINE_OPTIONS, "weight": Opt(2.0, "grosor (x línea base)", lo=0.5, hi=6.0)}

    def line_specs(self, o):
        return [(o["weight"], 0.0)]


@register("frame", "doble")
class DoubleFrame(LineFrame):
    doc = "Dos líneas concéntricas: una gruesa y una fina."
    options = {**_LINE_OPTIONS,
               "outer_weight": Opt(2.6, "grosor de la exterior (x línea base)", lo=0.5, hi=6.0),
               "inner_weight": Opt(1.0, "grosor de la interior (x línea base)", lo=0.5, hi=6.0),
               "gap_mm": Opt(0.9, "separación entre las dos líneas", lo=0.3, hi=3.0)}

    def line_specs(self, o):
        return [(o["outer_weight"], 0.0), (o["inner_weight"], o["gap_mm"])]


class BandFrame(Frame):
    """Marcos con banda ornamental. Subclases: ``motif_<nombre>`` (lado) y ``corner_motif`` (esquina)."""

    def build(self, ctx):
        o = self.o
        t = o["band_mm"]
        line_color, fill = ctx.color(o["color"]), ctx.color(o["fill"])
        outer = ctx.field.inset(o["inset_mm"])
        inner = outer.inset(t)
        prims = []
        for side, length in self.sides(outer, t):
            n = max(1, round(length / (t * o["unit_ratio"])))
            unit = length / n
            prims.append(self._transformed_rect(side, length, t, fill))
            for k in range(n):
                shift = Affine.translate(k * unit, 0).then(side)
                prims += transform_all(self.motif(ctx, unit, t), shift)
        for cx0, cy0 in ((outer.x0, outer.y0), (outer.x1 - t, outer.y0), (outer.x1 - t, outer.y1 - t), (outer.x0, outer.y1 - t)):
            prims.append(poly([(cx0, cy0), (cx0 + t, cy0), (cx0 + t, cy0 + t), (cx0, cy0 + t)], fill=fill))
            prims += transform_all(self.corner_motif(ctx, t), Affine.translate(cx0, cy0))
        prims.append(poly(outer.corners(), stroke=line_color, width=ctx.weight(o["outer_weight"])))
        prims.append(poly(inner.corners(), stroke=line_color, width=ctx.weight(o["inner_weight"])))
        pad_rect = inner.inset(o["pad_mm"])
        return FrameResult(prims, self.field_outline(ctx.field), pad_rect.corners(), pad_rect)

    @staticmethod
    def sides(outer: Rect, t: float):
        """Afines de coordenadas locales a página para los cuatro lados, con su longitud útil."""
        return [
            (Affine(1, 0, 0, 1, outer.x0 + t, outer.y0), outer.w - 2 * t),         # arriba
            (Affine(0, -1, 1, 0, outer.x1, outer.y0 + t), outer.h - 2 * t),        # derecha
            (Affine(-1, 0, 0, -1, outer.x1 - t, outer.y1), outer.w - 2 * t),       # abajo
            (Affine(0, 1, -1, 0, outer.x0, outer.y1 - t), outer.h - 2 * t),        # izquierda
        ]

    @staticmethod
    def _transformed_rect(side, length, t, fill):
        return poly([side(p) for p in ((0, 0), (length, 0), (length, t), (0, t))], fill=fill)

    def motif(self, ctx, unit, t):
        return getattr(self, "motif_" + self.o["motif"])(ctx, unit, t)

    def corner_motif(self, ctx, t):
        raise NotImplementedError


_BAND_OPTIONS = {
    "color": Opt("primary", "color de las líneas y motivos", color=True, rand=False),
    "fill": Opt("secondary", "color de fondo de la banda", color=True),
    "accent": Opt("accent", "color de los detalles", color=True),
    "inset_mm": Opt(1.0, "distancia del campo al marco", lo=0.0, hi=4.0),
    "pad_mm": Opt(0.9, "aire entre la banda y el interior", lo=0.0, hi=4.0),
    "outer_weight": Opt(1.8, "grosor de la línea exterior (x línea base)", lo=0.5, hi=6.0),
    "inner_weight": Opt(1.0, "grosor de la línea interior (x línea base)", lo=0.5, hi=6.0),
}


@register("frame", "geometrico")
class GeometricFrame(BandFrame):
    doc = "Banda con un motivo geométrico repetido: rombos, dientes, cuadros, puntos o escalones."
    options = {**_BAND_OPTIONS,
               "motif": Opt("rombos", "motivo de la banda", choices=("rombos", "dientes", "cuadros", "puntos", "escalones")),
               "band_mm": Opt(3.4, "ancho de la banda", lo=1.5, hi=7.0, rlo=2.6, rhi=4.2),
               "unit_ratio": Opt(1.0, "largo de cada motivo respecto del ancho", lo=0.5, hi=2.5, rlo=0.8, rhi=1.4)}

    def motif_rombos(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        return [poly([(u / 2, t * 0.1), (u * 0.92, t / 2), (u / 2, t * 0.9), (u * 0.08, t / 2)], fill=c),
                poly([(u / 2, t * 0.32), (u * 0.62, t / 2), (u / 2, t * 0.68), (u * 0.38, t / 2)], fill=a)]

    def motif_dientes(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        return [poly([(0, 0), (u, 0), (u / 2, t * 0.92)], fill=c),
                poly([(0, t), (u / 2, t), (0, t * 0.1)], fill=a),
                poly([(u, t), (u / 2, t), (u, t * 0.1)], fill=a)]

    def motif_cuadros(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        h = min(u, t) * 0.36
        return [poly([(u / 2 - h, t / 2 - h), (u / 2 + h, t / 2 - h), (u / 2 + h, t / 2 + h), (u / 2 - h, t / 2 + h)],
                     stroke=c, width=ctx.weight(1.2)),
                circle(u / 2, t / 2, h * 0.4, fill=a)]

    def motif_puntos(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        r = min(u, t) * 0.3
        return [circle(u / 2, t / 2, r, fill=c), circle(u / 2, t / 2, r * 0.45, fill=a)]

    def motif_escalones(self, ctx, u, t):
        c = ctx.color(self.o["color"])
        widths = (0.14, 0.28, 0.42, 0.28, 0.14)
        rows = len(widths)
        left, right = [], []
        for k, w in enumerate(widths):
            y0, y1 = t * (0.1 + 0.8 * k / rows), t * (0.1 + 0.8 * (k + 1) / rows)
            left += [(u / 2 - w * u, y0), (u / 2 - w * u, y1)]
            right += [(u / 2 + w * u, y0), (u / 2 + w * u, y1)]
        return [poly(left + right[::-1], fill=c)]

    def corner_motif(self, ctx, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        return [poly([(t / 2, t * 0.1), (t * 0.9, t / 2), (t / 2, t * 0.9), (t * 0.1, t / 2)], fill=c),
                circle(t / 2, t / 2, t * 0.16, fill=a)]


@register("frame", "ornamentado")
class OrnamentedFrame(BandFrame):
    doc = "Banda con festones, perlas, hojas o cadeneta y una roseta en cada esquina."
    options = {**_BAND_OPTIONS,
               "motif": Opt("festones", "motivo de la banda", choices=("festones", "perlas", "hojas", "cadeneta")),
               "band_mm": Opt(4.2, "ancho de la banda", lo=2.0, hi=8.0, rlo=3.6, rhi=5.0),
               "unit_ratio": Opt(1.2, "largo de cada motivo respecto del ancho", lo=0.6, hi=2.5, rlo=1.0, rhi=1.5),
               "petals": Opt(8, "pétalos de la roseta de esquina", lo=6, hi=12)}

    def motif_festones(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        r = min(u / 2 * 0.94, t * 0.92)
        arch = [(u / 2 + math.cos(th) * r, math.sin(th) * r) for th in (math.pi * k / 24 for k in range(25))]
        inner = [(u / 2 + math.cos(th) * r * 0.55, math.sin(th) * r * 0.55) for th in (math.pi * k / 24 for k in range(25))]
        return [poly(arch, fill=c), poly(inner, fill=ctx.color(self.o["fill"])),
                circle(u / 2, r * 0.22, r * 0.14, fill=a)]

    def motif_perlas(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        r = min(u, t) * 0.36
        return [line([(0, t * 0.12), (u, t * 0.12)], c, ctx.weight(0.8)),
                line([(0, t * 0.88), (u, t * 0.88)], c, ctx.weight(0.8)),
                circle(u / 2, t / 2, r, fill=c), circle(u / 2, t / 2, r * 0.4, fill=a)]

    def motif_hojas(self, ctx, u, t):
        c = ctx.color(self.o["color"])
        bulge = min(u, t) * 0.13
        return [poly(lens((u * 0.04, t * 0.92), (u / 2, t * 0.1), bulge), fill=c),
                poly(lens((u * 0.96, t * 0.92), (u / 2, t * 0.1), bulge), fill=c)]

    def motif_cadeneta(self, ctx, u, t):
        c, a = ctx.color(self.o["color"]), ctx.color(self.o["accent"])
        r = min(u * 0.6, t * 0.42)
        return [circle(0, t / 2, r, stroke=c, width=ctx.weight(1.0)),
                circle(u, t / 2, r, stroke=c, width=ctx.weight(1.0)),
                circle(u / 2, t / 2, r, stroke=c, width=ctx.weight(1.0)),
                circle(u / 2, t / 2, r * 0.3, fill=a)]

    def corner_motif(self, ctx, t):
        c, a, f = ctx.color(self.o["color"]), ctx.color(self.o["accent"]), ctx.color(self.o["fill"])
        return rosette(t / 2, t / 2, t * 0.46, self.o["petals"], f, c, ctx.weight(0.9), dot=a, ring=c)
