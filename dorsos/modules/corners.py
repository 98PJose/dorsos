"""Ornamentos de esquina. Se diseñan para la esquina superior izquierda y se reflejan a las otras tres."""
import math

from ..geometry import Affine, arc, diamond, lens
from ..primitives import circle, line, poly, transform_all
from ..registry import register
from .base import Module, Opt
from .motifs import rosette


class Corners(Module):
    common = {
        "size_mm": Opt(9.0, "tamaño del ornamento", lo=3.0, hi=20.0, rlo=6.0, rhi=11.0),
        "line": Opt("primary", "color del trazo", color=True, rand=False),
        "fill": Opt("secondary", "color de los rellenos", color=True),
        "dot": Opt("accent", "color de los detalles", color=True),
        "clear": Opt(True, "despejar el fondo bajo el ornamento"),
    }

    def build(self, ctx):
        f = ctx.field
        size = self.o["size_mm"]
        colors = tuple(ctx.color(self.o[k]) for k in ("line", "fill", "dot"))
        local = []
        if self.o["clear"]:
            local.append(poly([(0, 0)] + arc(0, 0, size * 1.08, 0, math.pi / 2), fill=ctx.palette["background"]))
        local += self.ornament(ctx, size, *colors)
        placements = (Affine.translate(f.x0, f.y0), Affine(-1, 0, 0, 1, f.x1, f.y0),
                      Affine(-1, 0, 0, -1, f.x1, f.y1), Affine(1, 0, 0, -1, f.x0, f.y1))
        prims = []
        for aff in placements:
            prims += transform_all(local, aff)
        return prims

    def ornament(self, ctx, size, ln, fl, dt):
        raise NotImplementedError


@register("corners", "cuarto_circulo")
class QuarterCircles(Corners):
    doc = "Cuartos de círculo concéntricos."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        levels = 2 + round(ctx.density * 2)
        w = ctx.weight(1.0)
        out = []
        for k in range(levels):
            r = size * (1 - k / levels)
            out.append(poly([(0, 0)] + arc(0, 0, r, 0, math.pi / 2), fill=fl if k % 2 == 0 else None, stroke=ln, width=w))
        out.append(circle(size * 0.12, size * 0.12, size * 0.06, fill=dt))
        return out


@register("corners", "abanico")
class Fan(Corners):
    doc = "Abanico de radios con festón exterior."
    options = {**Corners.common, "rays": Opt(7, "radios", lo=3, hi=12)}

    def ornament(self, ctx, size, ln, fl, dt):
        n, w = self.o["rays"], ctx.weight(1.0)
        out = [poly([(0, 0)] + arc(0, 0, size, 0, math.pi / 2), fill=fl, stroke=ln, width=w)]
        for k in range(n + 1):
            a = math.pi / 2 * k / n
            out.append(line([(size * 0.15 * math.cos(a), size * 0.15 * math.sin(a)),
                             (size * math.cos(a), size * math.sin(a))], ln, w * 0.7))
        for k in range(n):
            a = math.pi / 2 * (k + 0.5) / n
            out.append(circle(size * 0.72 * math.cos(a), size * 0.72 * math.sin(a), size * 0.035, fill=dt))
        out.append(circle(0, 0, size * 0.15, fill=ln))
        return out


@register("corners", "roseta")
class CornerRosette(Corners):
    doc = "Roseta entera apoyada en la esquina."
    options = {**Corners.common, "petals": Opt(8, "pétalos", lo=5, hi=12)}

    def ornament(self, ctx, size, ln, fl, dt):
        c = size * 0.52
        return rosette(c, c, size * 0.48, self.o["petals"], fl, ln, ctx.weight(1.0), dot=dt, ring=ln)


@register("corners", "rombos")
class CornerDiamonds(Corners):
    doc = "Racimo de rombos y puntos."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        w = ctx.weight(1.0)
        return [poly(diamond(size * 0.36, size * 0.36, size * 0.32), fill=fl, stroke=ln, width=w),
                poly(diamond(size * 0.36, size * 0.36, size * 0.15), fill=dt),
                poly(diamond(size * 0.82, size * 0.16, size * 0.1), fill=ln),
                poly(diamond(size * 0.16, size * 0.82, size * 0.1), fill=ln),
                circle(size * 0.76, size * 0.52, size * 0.04, fill=dt),
                circle(size * 0.52, size * 0.76, size * 0.04, fill=dt)]


@register("corners", "hojas")
class CornerLeaves(Corners):
    doc = "Hojas que salen de la esquina en abanico."
    options = {**Corners.common, "leaves": Opt(3, "hojas", lo=2, hi=6)}

    def ornament(self, ctx, size, ln, fl, dt):
        n, w = self.o["leaves"], ctx.weight(1.0)
        out = []
        for k in range(n):
            a = math.pi / 2 * (k + 0.5) / n
            tip = (size * 0.95 * math.cos(a), size * 0.95 * math.sin(a))
            out.append(poly(lens((size * 0.1 * math.cos(a), size * 0.1 * math.sin(a)), tip, size * 0.11 * 3 / n),
                            fill=fl, stroke=ln, width=w))
        out.append(circle(0, 0, size * 0.13, fill=dt, stroke=ln, width=w))
        return out
