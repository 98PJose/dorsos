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


def diagonal_constants(field: Rect, s: float, down: bool) -> list[float]:
    """Constantes ``c`` de las rectas ``x + y = c`` (``down``) o ``x - y = c`` que cruzan el campo.

    Se anclan en el centro de la carta: el espejo cambia una familia por la otra y el
    conjunto de rectas queda invariante, así que la malla sale simétrica.
    """
    center = field.cx + field.cy if down else field.cx - field.cy
    lo = field.x0 + field.y0 if down else field.x0 - field.y1
    hi = field.x1 + field.y1 if down else field.x1 - field.y0
    return [center + k * s for k in range(math.floor((lo - center) / s), math.ceil((hi - center) / s) + 1)]


def rows(field: Rect, height: float, pad: int = 1) -> list[tuple[int, float]]:
    """``(j, y)`` del borde superior de cada fila de alto ``height``, centradas en el campo."""
    j0 = math.floor((field.y0 - field.cy) / height) - pad
    j1 = math.ceil((field.y1 - field.cy) / height) + pad
    return [(j, field.cy + j * height) for j in range(j0, j1 + 1)]


class StaggeredLattice:
    """Retícula al tresbolillo centrada en el campo: las filas impares van media celda a la derecha.

    ``s`` es el ancho de celda (un número entero de ellas cubre el ancho del campo) y
    ``dy = s * row_ratio`` la separación entre filas. Las filas pares se anclan en el centro
    y ``j`` y ``-j`` tienen la misma paridad, así que la retícula ya es simétrica respecto de
    los dos ejes del campo.
    """

    def __init__(self, field: Rect, nominal: float, row_ratio: float):
        self.field = field
        self.s = field.w / max(1, round(field.w / nominal))
        self.dy = self.s * row_ratio

    def cells(self, pad=1):
        """``(i, j, x, y)`` de cada celda que roza el campo, con ``pad`` celdas de margen."""
        f = self.field
        for j in range(math.floor((f.y0 - f.cy) / self.dy) - pad, math.ceil((f.y1 - f.cy) / self.dy) + pad + 1):
            x0 = f.cx + (j % 2) * self.s / 2
            for i in range(math.floor((f.x0 - x0) / self.s) - pad, math.ceil((f.x1 - x0) / self.s) + pad + 1):
                yield i, j, x0 + i * self.s, f.cy + j * self.dy


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
            x, y = lat.center(i, j) if self.sub == 1 else lat.pos(i, j)
            prims += self.tile(ctx, lat, x, y, i, j, self.cell_colors(ctx, i, j))
        return prims

    def cell_colors(self, ctx, i, j):
        """``(trazo, relleno, detalle)`` de una celda, con el intercambio de ``variation``."""
        o = self.o
        line, fill = o["line"], o["fill"]
        if o["variation"] > 0 and ctx.rng(i, j).random() < o["variation"]:
            line, fill = fill, line
        return ctx.color(line), ctx.color(fill), ctx.color(o["dot"])

    def indices(self, lat):
        return lat.indices()

    def levels(self, ctx, lo=1, hi=4):
        """Niveles de detalle (contornos anidados, pétalos extra...) según la densidad."""
        return lo + round(ctx.density * (hi - lo))

    def tile(self, ctx, lat, x, y, i, j, colors):
        raise NotImplementedError
