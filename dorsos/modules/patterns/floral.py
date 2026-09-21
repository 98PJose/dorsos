"""Patrones florales y de arabescos: rosetas y arabescos (volutas, ogivas)."""
import math

from ...geometry import Affine, TAU, arc, diamond, spiral
from ...primitives import circle, line, poly, transform_all
from ...registry import register
from ..base import Opt
from ..motifs import petals, rosette, star
from .base import Pattern


@register("pattern", "rosetas")
class Rosetas(Pattern):
    doc = "Rosetas, estrellas o anillos con rombos en los nudos de la retícula; 'mosaico' alterna roseta y estrella."
    options = {**Pattern.common,
               "cell_mm": Opt(7.0, "lado de cada celda", lo=3.0, hi=18.0, rand=False),
               "style": Opt("roseta", "variante", choices=("roseta", "estrella", "anillos", "mosaico")),
               "petals": Opt(8, "pétalos o puntas", lo=4, hi=16, rlo=6, rhi=12)}

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        n = self.o["petals"]
        style = self.o["style"]
        if style == "mosaico":
            style = "roseta" if (i + j) % 2 == 0 else "estrella"
        out = []
        if style == "roseta":
            out += rosette(x, y, s * 0.46, n, fl, ln, w, dot=dt, ring=ln)
            if self.levels(ctx) > 2:
                out.append(circle(x, y, s * 0.2, stroke=ln, width=w * 0.8))
        elif style == "estrella":
            out.append(star(x, y, s * 0.47, n, 0.5, fl, ln, w))
            out.append(circle(x, y, s * 0.13, fill=dt))
            if self.levels(ctx) > 2:
                out.append(star(x, y, s * 0.24, n, 0.55, None, ln, w * 0.8))
        else:  # anillos
            levels = self.levels(ctx, 2, 4)
            for k in range(levels):
                out.append(circle(x, y, s * 0.44 * (1 - k / levels), stroke=ln, width=w))
            for k in range(n):
                a = TAU * k / n
                out.append(line([(x + s * 0.3 * math.cos(a), y + s * 0.3 * math.sin(a)),
                                 (x + s * 0.44 * math.cos(a), y + s * 0.44 * math.sin(a))], ln, w * 0.8))
            out.append(circle(x, y, s * 0.09, fill=dt))
        # rombo en el nudo inferior derecho: cada nudo lo comparten cuatro celdas
        out.append(poly(diamond(x + s / 2, y + s / 2, s * 0.1), fill=dt if style != "anillos" else fl,
                        stroke=ln, width=w * 0.7))
        return out


@register("pattern", "arabescos")
class Arabescos(Pattern):
    doc = "Arabescos: volutas en cuatro cuadrantes u ogivas (círculos y estrellas cóncavas)."
    options = {**Pattern.common,
               "cell_mm": Opt(10.0, "lado de cada celda", lo=5.0, hi=22.0, rand=False),
               "style": Opt("volutas", "variante", choices=("volutas", "ogivas")),
               "turns": Opt(1.5, "vueltas de cada voluta", lo=1.0, hi=2.5)}

    def tile(self, ctx, lat, x, y, i, j, colors):
        if self.o["style"] == "volutas":
            return self.volutas(ctx, lat, x, y, colors)
        return self.ogivas(ctx, lat, x, y, colors)

    def volutas(self, ctx, lat, x, y, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        # Cuadrante (+,+): espiral que arranca junto al centro y se enrolla hacia fuera del eje.
        q = (s * 0.25, s * 0.25)
        curl = spiral(q[0], q[1], s * 0.19, s * 0.035, math.radians(225), self.o["turns"], direction=1)
        stem = [(0.0, s * 0.04), (s * 0.05, s * 0.06), curl[0]]
        one = [line(stem[:-1] + curl, ln, w * 1.3), circle(*curl[-1], s * 0.03, fill=dt)]
        out = []
        for m in (Affine(), Affine.mirror_x(0), Affine.mirror_y(0), Affine.rotate(math.pi)):
            out += transform_all(one, m.then(Affine.translate(x, y)))
        out.append(poly(diamond(x, y, s * 0.06), fill=fl, stroke=ln, width=w * 0.7))
        # flor de cuatro hojas en el nudo inferior derecho
        vx, vy = x + s / 2, y + s / 2
        out += petals(vx, vy, s * 0.03, s * 0.2, 4, fl, ln, w * 0.8, rot=math.pi / 4)
        out.append(circle(vx, vy, s * 0.045, fill=dt))
        return out

    def ogivas(self, ctx, lat, x, y, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        half = s / 2
        # Estrella cóncava: la región de la celda que dejan los cuatro cuartos de círculo de las esquinas.
        star_pts = []
        # recorrido continuo: derecha -> arriba -> izquierda -> abajo -> derecha
        for (cx, cy), a0 in (((x + half, y - half), math.pi / 2), ((x - half, y - half), 0.0),
                              ((x - half, y + half), 1.5 * math.pi), ((x + half, y + half), math.pi)):
            star_pts += arc(cx, cy, half, a0, a0 + math.pi / 2)
        out = [poly(star_pts, fill=fl, stroke=ln, width=w)]
        levels = self.levels(ctx)
        for k in range(1, levels):
            out.append(poly([(x + (px - x) * (1 - k / levels), y + (py - y) * (1 - k / levels)) for px, py in star_pts],
                            stroke=ln, width=w * 0.7))
        out.append(circle(x, y, s * 0.07, fill=dt))
        vx, vy = x + half, y + half
        out.append(circle(vx, vy, half * 0.6, stroke=ln, width=w))
        out.append(circle(vx, vy, half * 0.25, fill=dt))
        return out
