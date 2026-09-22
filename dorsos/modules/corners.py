"""Ornamentos de esquina. Se diseñan para la esquina superior izquierda y se reflejan a las otras tres."""
import math

from ..geometry import Affine, arc, diamond, lens, spiral, star_polygon
from ..primitives import circle, line, poly, transform_all
from ..registry import register
from .base import Module, Opt
from .motifs import fleur_de_lis, rosette


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


@register("corners", "escuadra")
class CornerBracket(Corners):
    doc = "Escuadra: dos ángulos paralelos con remates redondos, como los herrajes de esquina."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        s, bar = size, size * 0.13
        inner, thin = size * 0.27, size * 0.07
        return [poly(_box(0, 0, s, bar), fill=ln), poly(_box(0, 0, bar, s), fill=ln),
                poly(_box(inner, inner, s * 0.78, inner + thin), fill=ln),
                poly(_box(inner, inner, inner + thin, s * 0.78), fill=ln),
                circle(s, bar / 2, bar * 0.75, fill=dt), circle(bar / 2, s, bar * 0.75, fill=dt),
                poly(diamond(s * 0.56, s * 0.56, s * 0.1), fill=dt)]


@register("corners", "volutas")
class CornerScrolls(Corners):
    doc = "Dos volutas simétricas respecto de la diagonal, unidas por un arco."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        w = ctx.weight(1.4)
        r, mid = size * 0.2, size * 0.42
        # voluta a lo largo del borde de arriba; la otra es su reflejo en la diagonal
        curl = spiral(size * 0.62, mid - r, r, r * 0.2, math.pi, 1.2, direction=-1)
        mirrored = [(y, x) for x, y in curl]
        joint = arc(mid, mid, r, math.pi, 1.5 * math.pi)
        return [line(curl, ln, w), line(mirrored, ln, w), line(joint, ln, w),
                circle(size * 0.62, mid - r, size * 0.05, fill=dt), circle(mid - r, size * 0.62, size * 0.05, fill=dt)]


@register("corners", "estrella")
class CornerStar(Corners):
    doc = "Estrella de ocho puntas apoyada en la esquina."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        c, r, w = size * 0.5, size * 0.46, ctx.weight(1.0)
        return [poly(star_polygon(c, c, r, r * 0.45, 8), fill=fl, stroke=ln, width=w),
                poly(star_polygon(c, c, r * 0.5, r * 0.25, 8), fill=ln),
                circle(c, c, r * 0.12, fill=dt)]


@register("corners", "lis")
class CornerLis(Corners):
    doc = "Flor de lis en diagonal, con la punta hacia el centro de la carta."
    options = {**Corners.common}

    def ornament(self, ctx, size, ln, fl, dt):
        # La lis se dibuja con la punta hacia arriba; girada 135° apunta hacia dentro.
        place = Affine.rotate(3 * math.pi / 4).then(Affine.translate(size * 0.48, size * 0.48))
        return transform_all(fleur_de_lis(0, 0, size * 0.5, ln, dt), place)


def _box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
