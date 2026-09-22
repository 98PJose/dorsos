"""Patrones florales y de arabescos: rosetas y arabescos (volutas, ogivas)."""
import math

from ...geometry import Affine, TAU, arc, diamond, lens, spiral
from ...primitives import circle, line, poly, transform_all
from ...registry import register
from ..base import Opt
from ..motifs import flared_cross, fleur_de_lis, petals, rosette, star
from .base import Pattern, StaggeredLattice


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


@register("pattern", "damasco")
class Damasco(Pattern):
    doc = "Damasco de mandorlas ojivales al tresbolillo: vacías, con flor o alternando relleno."
    options = {**Pattern.common,
               "cell_mm": Opt(9.0, "ancho de cada mandorla", lo=4.0, hi=22.0, rand=False),
               "style": Opt("ojiva", "variante", choices=("ojiva", "flor", "alternado")),
               "petals": Opt(6, "pétalos de la flor interior", lo=4, hi=12)}

    ROW_RATIO = 1.05  # las filas casi se tocan, como en un damasco de tela

    def build(self, ctx):
        o = self.o
        lat = StaggeredLattice(ctx.field, o["cell_mm"] * ctx.scale, self.ROW_RATIO)
        s, w = lat.s, ctx.weight(o["weight"])
        half, tall = s * 0.42, s * 0.56
        prims = []
        for i, j, x, y in lat.cells():
            ln, fl, dt = self.cell_colors(ctx, i, j)
            shape = lens((x, y - tall), (x, y + tall), half)
            filled = o["style"] == "alternado" and (i + j) % 2 == 0
            prims.append(poly(shape, fill=fl if filled else None, stroke=ln, width=w))
            if o["style"] == "flor":
                prims += petals(x, y, s * 0.06, s * 0.3, o["petals"], fl, ln, w * 0.8)
                prims.append(circle(x, y, s * 0.07, fill=dt))
            else:
                prims.append(poly(lens((x, y - tall * 0.6), (x, y + tall * 0.6), half * 0.55),
                                  stroke=ln, width=w * 0.8))
                prims.append(circle(x, y, s * 0.06, fill=dt))
            # Los huecos de una retícula al tresbolillo están a un cuarto de celda a cada
            # lado, no a media: el par simétrico es lo que hace que la malla lo sea.
            for side in (-1, 1):
                prims.append(poly(diamond(x + side * s / 4, y + lat.dy / 2, s * 0.09, lat.dy * 0.11), fill=dt))
        return prims


@register("pattern", "sembrado")
class Sembrado(Pattern):
    doc = "Motivo suelto sembrado al tresbolillo: flor de lis, trébol, cruz o lunares."
    options = {**Pattern.common,
               "cell_mm": Opt(8.0, "separación entre motivos", lo=3.0, hi=20.0, rand=False),
               "style": Opt("flor_de_lis", "variante", choices=("flor_de_lis", "trebol", "cruz", "lunares"))}

    ROW_RATIO = 0.95

    def build(self, ctx):
        o = self.o
        lat = StaggeredLattice(ctx.field, o["cell_mm"] * ctx.scale, self.ROW_RATIO)
        s, w = lat.s, ctx.weight(o["weight"])
        r = s * 0.34
        prims = []
        for i, j, x, y in lat.cells():
            ln, fl, dt = self.cell_colors(ctx, i, j)
            prims += getattr(self, "motif_" + o["style"])(x, y, r, ln, fl, dt, w)
        return prims

    @staticmethod
    def motif_flor_de_lis(x, y, r, ln, fl, dt, w):
        return fleur_de_lis(x, y, r, ln, dt)

    @staticmethod
    def motif_trebol(x, y, r, ln, fl, dt, w):
        out = [line([(x, y + r * 0.2), (x, y + r)], ln, w * 1.4)]
        for k in range(3):
            a = -math.pi / 2 + TAU * k / 3
            out.append(circle(x + r * 0.38 * math.cos(a), y + r * 0.38 * math.sin(a), r * 0.36,
                              fill=fl, stroke=ln, width=w))
        out.append(circle(x, y, r * 0.12, fill=dt))
        return out

    @staticmethod
    def motif_cruz(x, y, r, ln, fl, dt, w):
        return [poly(flared_cross(x, y, r, r * 0.2, r * 0.42), fill=ln), circle(x, y, r * 0.14, fill=dt)]

    @staticmethod
    def motif_lunares(x, y, r, ln, fl, dt, w):
        # el lunar pequeño va a media celda exacta: cualquier otra distancia rompe el espejo
        return [circle(x, y, r * 0.42, fill=ln), circle(x + r / 0.68, y, r * 0.16, fill=dt)]

