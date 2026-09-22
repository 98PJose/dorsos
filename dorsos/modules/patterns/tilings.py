"""Teselados: panal hexagonal y lacería mudéjar."""
import math

from ...geometry import box, diamond, regular_polygon, star_polygon
from ...primitives import circle, poly
from ...registry import register
from ..base import Opt
from ..motifs import rosette
from .base import Pattern, StaggeredLattice

HEX_ROW_RATIO = math.sqrt(3) / 2  # separación entre filas de un panal de ancho 1


@register("pattern", "panal")
class Panal(Pattern):
    doc = "Panal hexagonal: celdas vacías, con flor, con estrella o en cubos en relieve."
    options = {**Pattern.common,
               "cell_mm": Opt(7.0, "ancho de cada hexágono", lo=3.0, hi=20.0, rand=False),
               "style": Opt("simple", "variante", choices=("simple", "flor", "cubos", "estrellas"))}

    def build(self, ctx):
        o = self.o
        lat = StaggeredLattice(ctx.field, o["cell_mm"] * ctx.scale, HEX_ROW_RATIO)
        r = lat.s / math.sqrt(3)  # circunradio del hexágono de vértice arriba
        w = ctx.weight(o["weight"])
        prims = []
        for i, j, x, y in lat.cells():
            ln, fl, dt = self.cell_colors(ctx, i, j)
            hexagon = regular_polygon(x, y, r, 6)
            if o["style"] == "cubos":
                prims += self.cube(x, y, hexagon, ln, fl, dt)
                continue
            prims.append(poly(hexagon, stroke=ln, width=w))
            if o["style"] == "flor":
                prims += rosette(x, y, r * 0.66, 6, fl, ln, w * 0.8, dot=dt)
            elif o["style"] == "estrellas":
                prims.append(poly(star_polygon(x, y, r * 0.72, r * 0.36, 6), fill=fl, stroke=ln, width=w * 0.8))
                prims.append(circle(x, y, r * 0.14, fill=dt))
            else:
                for k in range(1, self.levels(ctx, 1, 3)):
                    prims.append(poly(regular_polygon(x, y, r * (1 - 0.22 * k), 6), stroke=ln, width=w * 0.8))
                prims.append(circle(x, y, r * 0.12, fill=dt))
        return prims

    @staticmethod
    def cube(x, y, hexagon, top, right, left):
        """Los tres rombos del hexágono, coloreados como las caras de un cubo visto de frente."""
        c = (x, y)
        v = hexagon  # v[0] arriba, el resto en sentido horario
        return [poly([c, v[5], v[0], v[1]], fill=top),
                poly([c, v[1], v[2], v[3]], fill=right),
                poly([c, v[3], v[4], v[5]], fill=left)]


@register("pattern", "mudejar")
class Mudejar(Pattern):
    doc = "Lacería mudéjar: estrellas de ocho puntas macizas, de trazo, u octógonos con cuadros."
    options = {**Pattern.common,
               "cell_mm": Opt(9.0, "lado de cada celda", lo=4.0, hi=22.0, rand=False),
               "style": Opt("estrellas", "variante", choices=("estrellas", "lazo", "octogonos"))}

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        style = self.o["style"]
        if style == "octogonos":
            # teselado de octógonos y cuadros: lado a, centros a a(1+raíz de 2)
            side = s / (1 + math.sqrt(2))
            out = [poly(regular_polygon(x, y, side / (2 * math.sin(math.pi / 8)), 8, rot=math.pi / 8),
                        fill=fl, stroke=ln, width=w)]
            out.append(poly(diamond(x + s / 2, y + s / 2, side * math.sqrt(2) / 2), fill=dt, stroke=ln, width=w))
            out.append(circle(x, y, side * 0.3, stroke=ln, width=w * 0.8))
            return out
        # estrella de ocho puntas: dos cuadrados girados 45°, con un rombo en cada hueco
        outer = s * 0.5 * math.sqrt(2) * 0.86
        star = star_polygon(x, y, outer, outer * 0.545, 8, rot=-math.pi / 2)
        gap = poly(box(x + s / 2, y + s / 2, s * 0.17), fill=dt if style == "estrellas" else None,
                   stroke=ln, width=w * 0.8)
        if style == "estrellas":
            return [poly(star, fill=ln), poly(star_polygon(x, y, outer * 0.45, outer * 0.25, 8), fill=fl), gap]
        out = [poly(star, stroke=ln, width=w)]
        for k in range(1, self.levels(ctx, 2, 3)):
            out.append(poly(star_polygon(x, y, outer * (1 - 0.3 * k), outer * 0.545 * (1 - 0.3 * k), 8),
                            stroke=ln, width=w * 0.8))
        out += [circle(x, y, s * 0.06, fill=dt), gap]
        return out
