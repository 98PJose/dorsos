"""Patrones geométricos: rombos y retícula."""
from ...geometry import box, diamond
from ...primitives import circle, line, poly
from ...registry import register
from ..base import Opt
from .base import Pattern


@register("pattern", "rombos")
class Rombos(Pattern):
    doc = "Malla de rombos (arlequín): concéntricos, alternados, cruzados o con puntos."
    sub = 2  # los rombos ocupan los nodos de paso s/2 con i + j par
    options = {**Pattern.common,
               "cell_mm": Opt(6.0, "ancho de cada rombo", lo=2.5, hi=16.0, rand=False),
               "style": Opt("concentricos", "variante", choices=("concentricos", "arlequin", "cruzado", "puntos"))}

    def indices(self, lat):
        return [(i, j) for i, j in lat.indices() if (i + j) % 2 == 0]

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        half = s / 2
        style = self.o["style"]
        out = []
        if style == "arlequin" and i % 2 == 0:  # i par/impar es el damero de la malla girada 45°
            out.append(poly(diamond(x, y, half), fill=fl))
        out.append(poly(diamond(x, y, half), stroke=ln, width=w))
        if style == "concentricos":
            levels = self.levels(ctx)
            for k in range(1, levels):
                out.append(poly(diamond(x, y, half * (1 - k / levels) * 0.92), stroke=ln, width=w * 0.8))
            out.append(poly(diamond(x, y, half * 0.22), fill=dt))
        elif style == "arlequin":
            out.append(poly(diamond(x, y, half * 0.6), stroke=ln, width=w * 0.8))
            out.append(poly(diamond(x, y, half * 0.2), fill=dt))
        elif style == "cruzado":
            for vx, vy in ((x + half, y), (x - half, y), (x, y + half), (x, y - half)):
                out.append(poly(diamond(vx, vy, s * 0.1), fill=dt))
            out.append(poly(diamond(x, y, half * 0.5), fill=fl, stroke=ln, width=w * 0.8))
        else:  # puntos
            out.append(circle(x, y, s * 0.11, fill=dt))
            for k in range(4):
                dx, dy = ((1, 0), (-1, 0), (0, 1), (0, -1))[k]
                out.append(circle(x + dx * half * 0.55, y + dy * half * 0.55, s * 0.045, fill=ln))
        return out


@register("pattern", "reticula")
class Reticula(Pattern):
    doc = "Retícula ortogonal: cuadros con motivo interior, líneas, cruces o damero."
    options = {**Pattern.common,
               "cell_mm": Opt(5.0, "lado de cada celda", lo=2.5, hi=14.0, rand=False),
               "style": Opt("cuadros", "variante", choices=("cuadros", "lineas", "cruces", "damero")),
               "inner": Opt("rombo", "motivo dentro del cuadro", choices=("cuadrado", "rombo", "circulo", "cruz", "ninguno"))}

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        half = s / 2
        style = self.o["style"]
        out = []
        if style == "cuadros":
            out.append(poly(box(x, y, half * 0.86), stroke=ln, width=w))
            for k in range(1, self.levels(ctx, 1, 3)):
                out.append(poly(box(x, y, half * (0.86 - 0.16 * k)), stroke=ln, width=w * 0.7))
            out += self._inner(x, y, half * 0.48, fl, dt)
        elif style == "lineas":
            out.append(poly(box(x, y, half), stroke=ln, width=w))
            out.append(circle(x, y, s * 0.09, fill=dt))
            for vx, vy in ((x - half, y - half), (x + half, y - half)):
                out.append(poly(diamond(vx, vy, s * 0.11), fill=fl, stroke=ln, width=w * 0.7))
        elif style == "cruces":
            arm = half * 0.62
            out.append(line([(x - arm, y), (x + arm, y)], ln, w * 1.6))
            out.append(line([(x, y - arm), (x, y + arm)], ln, w * 1.6))
            out.append(circle(x, y, s * 0.07, fill=dt))
            out.append(poly(diamond(x + half, y + half, s * 0.1), fill=fl, stroke=ln, width=w * 0.7))
        else:  # damero
            if (i + j) % 2 == 0:
                out.append(poly(box(x, y, half * 0.98), fill=fl))
                out.append(poly(box(x, y, half * 0.5), stroke=ln, width=w))
            else:
                out.append(circle(x, y, s * 0.16, fill=dt))
                out.append(circle(x, y, s * 0.3, stroke=ln, width=w))
        return out

    def _inner(self, x, y, r, fill, dot):
        kind = self.o["inner"]
        if kind == "cuadrado":
            return [poly(box(x, y, r * 0.85), fill=fill), circle(x, y, r * 0.25, fill=dot)]
        if kind == "rombo":
            return [poly(diamond(x, y, r * 1.1), fill=fill), circle(x, y, r * 0.25, fill=dot)]
        if kind == "circulo":
            return [circle(x, y, r * 0.9, fill=fill), circle(x, y, r * 0.3, fill=dot)]
        if kind == "cruz":
            arm, thick = r * 1.0, r * 0.32
            return [poly(box(x, y, arm, thick), fill=fill), poly(box(x, y, thick, arm), fill=fill),
                    circle(x, y, r * 0.22, fill=dot)]
        return []
