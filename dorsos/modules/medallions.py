"""Medallones centrales: contorno (círculo, óvalo, rombo, roseta, estrella, cuatrilóbulo) + motivo interior."""
import math

from ..geometry import circle_points, diamond, star_polygon, union_of_circles
from ..primitives import circle, poly
from ..registry import register
from .base import Module, Opt
from .motifs import petals, rosette, star

INTERIORS = ("roseta", "estrella", "rombo", "circulo", "flor", "ninguno")


class Medallion(Module):
    """Subclases: ``unit_outline()`` (contorno de semiancho 1) y la opción ``aspect``."""
    common = {
        "size": Opt(0.55, "ancho del medallón (fracción del ancho interior)", lo=0.25, hi=0.9, rlo=0.42, rhi=0.6),
        "line": Opt("primary", "color del trazo", color=True, rand=False),
        "fill": Opt("secondary", "color del fondo del medallón", color=True),
        "dot": Opt("accent", "color de los detalles", color=True),
        "halo": Opt("background", "color del halo que despeja el patrón", color=True, rand=False),
        "halo_mm": Opt(1.4, "anchura del halo", lo=0.0, hi=5.0, rlo=1.0, rhi=2.2),
        "rings": Opt(2, "contornos concéntricos", lo=1, hi=4, rhi=3),
        "interior": Opt("roseta", "motivo del interior", choices=INTERIORS),
        "beads": Opt(True, "perlas alrededor del contorno"),
        "petals": Opt(8, "pétalos o puntas del motivo interior", lo=4, hi=16, rlo=6, rhi=12),
    }

    def unit_outline(self):
        raise NotImplementedError

    def build(self, ctx):
        o = self.o
        cx, cy = ctx.field.cx, ctx.field.cy
        half = ctx.field.w * o["size"] / 2
        aspect = o["aspect"]
        ln, fl, dt, halo = (ctx.color(o[k]) for k in ("line", "fill", "dot", "halo"))
        w = ctx.weight(1.4)
        shape = self.unit_outline()

        def scaled(k):
            return [(cx + x * half * k, cy + y * half * k * aspect) for x, y in shape]

        prims = []
        if o["halo_mm"] > 0:
            prims.append(poly(scaled(1 + o["halo_mm"] / half), fill=halo))
        prims.append(poly(scaled(1.0), fill=fl, stroke=ln, width=w))
        for k in range(1, o["rings"]):
            prims.append(poly(scaled(1 - 0.09 * k), stroke=ln, width=w * 0.6))
        if o["beads"]:
            outline = scaled(1.0)
            n = 4 * max(4, round(half / 1.6))
            step = len(outline) / n
            for k in range(n):
                x, y = outline[int(k * step)]
                prims.append(circle(x, y, half * 0.035, fill=dt))
        prims += self.interior(ctx, cx, cy, half * (0.86 - 0.09 * o["rings"]) * 0.75)
        return prims

    def interior(self, ctx, cx, cy, r):
        o = self.o
        ln, fl, dt = ctx.color(o["line"]), ctx.color(o["fill"]), ctx.color(o["dot"])
        w, n = ctx.weight(1.0), o["petals"]
        kind = o["interior"]
        if kind == "roseta":
            return rosette(cx, cy, r, n, ln, fl, w, dot=dt, ring=ln)
        if kind == "estrella":
            return [star(cx, cy, r, n, 0.5, ln, fl, w), circle(cx, cy, r * 0.2, fill=dt)]
        if kind == "rombo":
            return [poly(diamond(cx, cy, r), fill=ln), poly(diamond(cx, cy, r * 0.55), fill=fl),
                    circle(cx, cy, r * 0.18, fill=dt)]
        if kind == "circulo":
            return [circle(cx, cy, r, fill=ln), circle(cx, cy, r * 0.62, fill=fl), circle(cx, cy, r * 0.25, fill=dt)]
        if kind == "flor":
            return (petals(cx, cy, r * 0.15, r, n, ln, fl, w, bulge=0.35)
                    + petals(cx, cy, r * 0.1, r * 0.55, n, dt, fl, w, rot=-math.pi / 2 + math.pi / n, bulge=0.35)
                    + [circle(cx, cy, r * 0.12, fill=fl)])
        return []


@register("medallion", "circulo")
class MedallionCircle(Medallion):
    doc = "Medallón circular."
    options = {**Medallion.common, "aspect": Opt(1.0, "alto / ancho", lo=0.7, hi=1.6, rand=False)}

    def unit_outline(self):
        return circle_points(0, 0, 1.0, 96)


@register("medallion", "ovalo")
class MedallionOval(MedallionCircle):
    doc = "Medallón oval, más alto que ancho."
    options = {**Medallion.common, "aspect": Opt(1.35, "alto / ancho", lo=0.7, hi=1.8, rand=False)}


@register("medallion", "rombo")
class MedallionDiamond(Medallion):
    doc = "Medallón en rombo."
    options = {**Medallion.common, "aspect": Opt(1.4, "alto / ancho", lo=0.7, hi=1.8, rand=False)}

    def unit_outline(self):
        return diamond(0, 0, 1.0)


@register("medallion", "roseta")
class MedallionRosette(Medallion):
    doc = "Medallón festoneado como una roseta de lóbulos circulares."
    options = {**Medallion.common, "aspect": Opt(1.0, "alto / ancho", lo=0.7, hi=1.6, rand=False),
               "lobes": Opt(10, "lóbulos del contorno", lo=5, hi=16)}

    def unit_outline(self):
        n = self.o["lobes"]
        sin = math.sin(math.pi / n)
        rho = sin / (1 + sin)  # lóbulos de radio rho a distancia 1 - rho: contiguos y tangentes al radio 1
        d = 1 - rho
        return union_of_circles([(d * math.cos(2 * math.pi * k / n), d * math.sin(2 * math.pi * k / n), rho * 1.25)
                                 for k in range(n)], samples=720)


@register("medallion", "cuatrilobulo")
class MedallionQuatrefoil(Medallion):
    doc = "Medallón de cuatro lóbulos."
    options = {**Medallion.common, "aspect": Opt(1.0, "alto / ancho", lo=0.7, hi=1.6, rand=False)}

    def unit_outline(self):
        return union_of_circles([(0.5 * math.cos(a), 0.5 * math.sin(a), 0.5)
                                 for a in (0, math.pi / 2, math.pi, 1.5 * math.pi)], samples=720)


@register("medallion", "estrella")
class MedallionStar(Medallion):
    doc = "Medallón en estrella de puntas."
    options = {**Medallion.common, "aspect": Opt(1.0, "alto / ancho", lo=0.7, hi=1.6, rand=False)}

    def unit_outline(self):
        return star_polygon(0, 0, 1.0, 0.72, self.o["petals"])
