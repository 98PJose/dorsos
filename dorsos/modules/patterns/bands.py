"""Patrones por bandas: espiga, greca griega y trenzados.

Las filas se anclan en el centro del campo, igual que las retículas. Las bandas de la
espiga y de la greca tienen sentido (suben hacia un lado), así que el espejo del dominio
fundamental las encuentra consigo mismas en el eje y forma una punta de flecha, como en un
parqué real.
"""
import math

from ...geometry import box, diagonal_segment
from ...primitives import line, poly
from ...registry import register
from ..base import Opt
from .base import Lattice, Pattern, diagonal_constants, rows


@register("pattern", "espiga")
class Espiga(Pattern):
    doc = "Espiga, galón de chevrones o zigzag de líneas finas."
    options = {**Pattern.common,
               "cell_mm": Opt(6.0, "ancho de cada diente", lo=2.5, hi=16.0, rand=False),
               "style": Opt("espiga", "variante", choices=("espiga", "galon", "zigzag"))}

    def build(self, ctx):
        o = self.o
        field = ctx.field
        s = Lattice(field, o["cell_mm"] * ctx.scale).s
        style = o["style"]
        height = s if style == "espiga" else s * 0.6
        w = ctx.weight(o["weight"])
        prims = []
        for j, y in rows(field, height):
            color, _, dot = self.cell_colors(ctx, 0, j)
            if style == "espiga":
                prims += self.herringbone(field, s, y, j, color, s * 0.3 * o["weight"])
            else:
                prims += self.chevron(field, s, height, y, color, style, w, height * 0.5 * o["weight"])
        return prims

    @staticmethod
    def herringbone(field, s, y, j, color, thickness):
        """Barras sueltas a ±45° que se alternan a lo largo de la fila."""
        out = []
        k0 = math.floor((field.x0 - field.cx) / s) - 1
        k1 = math.ceil((field.x1 - field.cx) / s) + 1
        for k in range(k0, k1 + 1):
            x = field.cx + k * s
            up = (k + j) % 2 == 0
            a, b = (x, y + s), (x + s, y)
            if not up:
                a, b = (x, y), (x + s, y + s)
            trim = 0.07  # el hueco entre barras es lo que las separa en la espiga
            p = (a[0] + (b[0] - a[0]) * trim, a[1] + (b[1] - a[1]) * trim)
            q = (a[0] + (b[0] - a[0]) * (1 - trim), a[1] + (b[1] - a[1]) * (1 - trim))
            out.append(line([p, q], color, thickness))
        return out

    @staticmethod
    def chevron(field, s, height, y, color, style, w, thickness):
        """Zigzag continuo de periodo ``s``; en ``galon`` es una banda gruesa."""
        k0 = math.floor((field.x0 - field.cx) / (s / 2)) - 1
        k1 = math.ceil((field.x1 - field.cx) / (s / 2)) + 1
        pts = [(field.cx + k * s / 2, y + (k % 2) * height) for k in range(k0, k1 + 1)]
        if style == "galon":
            return [line(pts, color, thickness)]
        return [line(pts, color, w), line([(x, py + height * 0.34) for x, py in pts], color, w * 0.7)]


@register("pattern", "greca")
class Greca(Pattern):
    doc = "Greca griega: meandro, onda corrida o almenado, en bandas continuas."
    options = {**Pattern.common,
               "cell_mm": Opt(8.0, "ancho de cada módulo", lo=4.0, hi=20.0, rand=False),
               "style": Opt("meandro", "variante", choices=("meandro", "olas", "almenado"))}

    # Cada módulo es una espiral abierta de ``u`` en ``u``, con un raíl continuo al pie.
    # Se dibujan abiertas y colgando del raíl a propósito: un módulo cerrado de cuatro
    # brazos recuerda demasiado a una esvástica.
    SPIRALS = {
        "meandro": [(0, 4), (0, 0), (3, 0), (3, 3), (1, 3), (1, 1), (2, 1)],
        "olas": [(0, 4), (0, 0), (2, 0), (2, 2), (1, 2)],
    }
    # El almenado no cuelga de un raíl: es una onda cuadrada que enlaza con la del módulo
    # siguiente, así que se dibuja como una sola polilínea por fila.
    MERLON = [(0, 4), (0, 0), (2, 0), (2, 4), (4, 4)]

    def build(self, ctx):
        o = self.o
        field = ctx.field
        s = Lattice(field, o["cell_mm"] * ctx.scale).s
        u = s / 4
        w = ctx.weight(o["weight"]) * 1.8
        prims = []
        for j, y in rows(field, s):
            color, _, _ = self.cell_colors(ctx, 0, j)
            flip = j % 2 == 1  # filas alternas en sentido contrario
            ks = range(math.floor((field.x0 - field.cx) / s) - 1, math.ceil((field.x1 - field.cx) / s) + 2)
            def place(a, b, k):
                x = field.cx + k * s
                return (x + (s - a * u if flip else a * u), y + b * u)
            if o["style"] == "almenado":
                prims.append(line([place(a, b, k) for k in ks for a, b in self.MERLON[:-1]], color, w))
                continue
            prims.append(line([(field.x0, y + 4 * u), (field.x1, y + 4 * u)], color, w))
            for k in ks:
                prims.append(line([place(a, b, k) for a, b in self.SPIRALS[o["style"]]], color, w))
        return prims


@register("pattern", "entrelazo")
class Entrelazo(Pattern):
    doc = "Trenzado con efecto de pasar por encima y por debajo: cestería o trenza diagonal."
    options = {**Pattern.common,
               "cell_mm": Opt(8.0, "lado de cada celda", lo=3.0, hi=20.0, rand=False),
               "style": Opt("cesteria", "variante", choices=("cesteria", "trenza")),
               "bars": Opt(3, "listones por celda en la cestería", lo=2, hi=4)}

    def build(self, ctx):
        if self.o["style"] == "trenza":
            return self.braid(ctx)
        return super().build(ctx)

    def tile(self, ctx, lat, x, y, i, j, colors):
        """Cestería: la celda lleva listones tumbados o de pie según su paridad."""
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        n = self.o["bars"]
        half, thick = s / 2, s / n * 0.42
        horizontal = (i + j) % 2 == 0
        out = []
        for k in range(n):
            offset = -half + s * (k + 0.5) / n
            if horizontal:
                out.append(poly(box(x, y + offset, half * 0.98, thick), fill=fl, stroke=ln, width=w))
            else:
                out.append(poly(box(x + offset, y, thick, half * 0.98), fill=fl, stroke=ln, width=w))
        return out

    def braid(self, ctx):
        """Dos familias de cintas diagonales; en la mitad de los cruces se repinta la de arriba."""
        o = self.o
        field = ctx.field
        s = Lattice(field, o["cell_mm"] * ctx.scale).s
        ln, fl, _ = (ctx.color(o[k]) for k in ("line", "fill", "dot"))
        w = ctx.weight(o["weight"])
        half = s * 0.17                 # medio ancho de la cinta
        delta = half * math.sqrt(2)     # lo que hay que mover la constante para ese ancho
        consts = {down: diagonal_constants(field, s, down) for down in (True, False)}

        prims = []
        for down in (True, False):
            for c in consts[down]:
                prims += self.ribbon(field, c, down, delta, half, ln, fl, w)
        for k, cu in enumerate(consts[True]):
            for m, cv in enumerate(consts[False]):
                x, y = (cu + cv) / 2, (cu - cv) / 2
                if (k + m) % 2 or not (field.x0 <= x <= field.x1 and field.y0 <= y <= field.y1):
                    continue
                prims += self.patch((x, y), delta, half, ln, fl, w)
        return prims

    @staticmethod
    def ribbon(field, c, down, delta, half, line_color, fill, w):
        """Cinta centrada en la recta ``c``: cuerpo grueso y las dos aristas."""
        body = diagonal_segment(field, c, down)
        if not body:
            return []
        out = [line(body, fill, 2 * half)]
        for side in (-delta, delta):
            edge = diagonal_segment(field, c + side, down)
            if edge:
                out.append(line(edge, line_color, w))
        return out

    @staticmethod
    def patch(point, delta, half, line_color, fill, w):
        """Trozo de la cinta descendente repintado sobre la otra, para que pase por encima."""
        x, y = point
        reach = half * 1.7  # cubre de sobra el ancho de la cinta cruzada
        def along(dx, dy):
            return [(x + dx - reach, y + dy + reach), (x + dx + reach, y + dy - reach)]
        out = [line(along(0, 0), fill, 2 * half)]
        for side in (-delta / 2, delta / 2):
            out.append(line(along(side, side), line_color, w))
        return out
