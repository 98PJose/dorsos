"""Base de los patrones: retícula centrada en la carta y opciones comunes.

La retícula se ancla al centro de la carta, de modo que es simétrica respecto de los
ejes por construcción, y su paso se ajusta para que un número entero de celdas ocupe
exactamente el ancho del campo. En vertical las celdas de los extremos quedan
cortadas por igual arriba y abajo, como en las barajas reales.
"""
import math

from ..base import Module, Opt
from ...geometry import Rect


def fit_count(length: float, nominal: float, odd: bool) -> int:
    """Número de celdas de tamaño cercano a ``nominal`` que caben en ``length``."""
    n = max(1, round(length / nominal))
    if odd and n % 2 == 0:
        n = n + 1 if length / nominal > n else max(1, n - 1)
    return n


class Lattice:
    """Retícula de paso ``step = s / sub`` centrada en el campo.

    ``s`` es el tamaño de la celda. Con ``sub=2`` los nodos caen en las mitades de la
    celda, útil para las mallas en rombo. Los índices ``(i, j)`` cuentan pasos.
    """

    def __init__(self, field: Rect, nominal: float, sub: int = 1, odd: bool = True):
        self.field = field
        nx_cells = fit_count(field.w, nominal, odd and sub == 1)
        self.s = field.w / nx_cells
        ny_cells = fit_count(field.h, self.s, odd and sub == 1)
        self.sub = sub
        self.step = self.s / sub
        self.nx, self.ny = nx_cells * sub, ny_cells * sub
        self.x0 = field.cx - self.nx * self.step / 2
        self.y0 = field.cy - self.ny * self.step / 2

    def pos(self, i, j):
        return self.x0 + i * self.step, self.y0 + j * self.step

    def center(self, i, j):
        """Centro de la celda ``(i, j)`` (solo con ``sub == 1``)."""
        return self.x0 + (i + 0.5) * self.step, self.y0 + (j + 0.5) * self.step

    def indices(self, pad=1):
        """Índices ``(i, j)`` de todos los nodos que rozan el campo, con ``pad`` pasos de margen."""
        i0 = math.floor((self.field.x0 - self.x0) / self.step) - pad
        i1 = math.ceil((self.field.x1 - self.x0) / self.step) + pad
        j0 = math.floor((self.field.y0 - self.y0) / self.step) - pad
        j1 = math.ceil((self.field.y1 - self.y0) / self.step) + pad
        return [(i, j) for j in range(j0, j1 + 1) for i in range(i0, i1 + 1)]


class Pattern(Module):
    """Patrón de celdas repetidas. Las subclases implementan ``tile`` y fijan ``sub``."""
    sub = 1
    common = {
        "line": Opt("primary", "color del trazo", color=True, rand=False),
        "fill": Opt("secondary", "color de los rellenos", color=True),
        "dot": Opt("accent", "color de los detalles", color=True),
        "weight": Opt(1.0, "grosor (x línea base)", lo=0.4, hi=3.0, rlo=0.8, rhi=1.4),
        "variation": Opt(0.0, "probabilidad de invertir los colores de una celda", lo=0.0, hi=1.0, rhi=0.25),
    }

    def build(self, ctx):
        o = self.o
        lat = Lattice(ctx.field, o["cell_mm"] * ctx.scale, self.sub)
        prims = []
        for i, j in self.indices(lat):
            rng = ctx.rng(i, j) if o["variation"] > 0 else None
            flip = rng is not None and rng.random() < o["variation"]
            line, fill = (o["fill"], o["line"]) if flip else (o["line"], o["fill"])
            colors = (ctx.color(line), ctx.color(fill), ctx.color(o["dot"]))
            x, y = lat.center(i, j) if self.sub == 1 else lat.pos(i, j)
            prims += self.tile(ctx, lat, x, y, i, j, colors)
        return prims

    def indices(self, lat):
        return lat.indices()

    def levels(self, ctx, lo=1, hi=4):
        """Niveles de detalle (contornos anidados, pétalos extra...) según la densidad."""
        return lo + round(ctx.density * (hi - lo))

    def tile(self, ctx, lat, x, y, i, j, colors):
        raise NotImplementedError
