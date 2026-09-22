"""Patrones geométricos: rombos, celosía y retícula."""
from ...geometry import box, diagonal_segment, diamond, star_polygon
from ...primitives import circle, line, poly
from ...registry import register
from ..base import Opt
from .base import Lattice, Pattern, diagonal_constants


@register("pattern", "rombos")
class Rombos(Pattern):
    doc = "Malla de rombos (arlequín): concéntricos, alternados, cruzados, con puntos o macizos."
    sub = 2  # los rombos ocupan los nodos de paso s/2 con i + j par
    options = {**Pattern.common,
               "cell_mm": Opt(6.0, "ancho de cada rombo", lo=2.5, hi=16.0, rand=False),
               "style": Opt("concentricos", "variante",
                            choices=("concentricos", "arlequin", "cruzado", "puntos", "macizo", "estrellado")),
               "gap": Opt(0.3, "hueco entre rombos macizos (fracción del rombo)", lo=0.1, hi=0.5,
                          rlo=0.22, rhi=0.38)}

    def indices(self, lat):
        return [(i, j) for i, j in lat.indices() if (i + j) % 2 == 0]

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        half = s / 2
        style = self.o["style"]
        if style in ("macizo", "estrellado"):
            return self.solid(half, x, y, ln, dt, concave=style == "estrellado")
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

    def solid(self, half, x, y, line_color, dot_color, concave):
        """Rombo macizo con canales de fondo y un rombo pequeño en el hueco entre cuatro.

        Los nudos de paridad impar son justo el centro de cada hueco; basta sembrar dos por
        celda (derecha y abajo) para cubrirlos todos sin repetir.
        """
        r = half * (1 - self.o["gap"])
        shape = star_polygon(x, y, r, r * 0.62, 4) if concave else diamond(x, y, r)
        out = [poly(shape, fill=line_color)]
        small = half * self.o["gap"] * 0.8
        for dx, dy in ((1, 0), (0, 1)):
            out.append(poly(diamond(x + dx * half, y + dy * half, small), fill=dot_color))
        return out


@register("pattern", "celosia")
class Celosia(Pattern):
    doc = "Celosía: líneas diagonales continuas que cruzan toda la carta formando rombos."
    options = {**Pattern.common,
               "cell_mm": Opt(5.0, "ancho de cada rombo de la malla", lo=2.0, hi=14.0, rand=False),
               "style": Opt("simple", "variante", choices=("simple", "doble", "puntos", "rombos"))}

    def build(self, ctx):
        o = self.o
        field = ctx.field
        s = Lattice(field, o["cell_mm"] * ctx.scale).s
        ln, fl, dt = (ctx.color(o[k]) for k in ("line", "fill", "dot"))
        style = o["style"]
        doubled = style == "doble"
        w = ctx.weight(o["weight"] * (1.0 if doubled else 1.6))
        offsets = (-s * 0.11, s * 0.11) if doubled else (0.0,)

        prims, crossings = [], {}
        for down in (True, False):
            crossings[down] = consts = diagonal_constants(field, s, down)
            for c in consts:
                for d in offsets:
                    segment = diagonal_segment(field, c + d, down)
                    if segment:
                        prims.append(line(segment, ln, w))
        if style in ("puntos", "rombos"):
            prims += self.nodes(field, s, crossings, fl, dt, ctx.weight(o["weight"]), style)
        return prims

    @staticmethod
    def nodes(field, s, crossings, fill, dot, w, style):
        """Adorno en cada cruce de las dos familias de rectas."""
        out = []
        for cu in crossings[True]:
            for cv in crossings[False]:
                x, y = (cu + cv) / 2, (cu - cv) / 2
                if not (field.x0 <= x <= field.x1 and field.y0 <= y <= field.y1):
                    continue
                if style == "puntos":
                    out.append(circle(x, y, s * 0.09, fill=dot))
                else:
                    out.append(poly(diamond(x, y, s * 0.2), fill=fill, stroke=dot, width=w * 0.7))
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
