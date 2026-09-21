"""Geometría 2D en milímetros: rectángulos, isometrías y generadores de contornos.

Convención: origen arriba a la izquierda, x hacia la derecha, y hacia abajo.
Todos los generadores devuelven listas de puntos ``(x, y)``.
"""
import math
from dataclasses import dataclass

from .constants import CIRCLE_SEGMENTS

Point = tuple[float, float]
TAU = 2 * math.pi


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def w(self):
        return self.x1 - self.x0

    @property
    def h(self):
        return self.y1 - self.y0

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2

    def inset(self, d):
        return Rect(self.x0 + d, self.y0 + d, self.x1 - d, self.y1 - d)

    def corners(self):
        """Esquinas en orden arriba-izq, arriba-der, abajo-der, abajo-izq."""
        return [(self.x0, self.y0), (self.x1, self.y0), (self.x1, self.y1), (self.x0, self.y1)]


@dataclass(frozen=True)
class Affine:
    """Transformación afín ``(x, y) -> (a x + b y + e, c x + d y + f)``."""
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def __call__(self, p: Point) -> Point:
        x, y = p
        return (self.a * x + self.b * y + self.e, self.c * x + self.d * y + self.f)

    def then(self, other: "Affine") -> "Affine":
        """Composición: primero ``self`` y después ``other``."""
        return Affine(
            other.a * self.a + other.b * self.c, other.a * self.b + other.b * self.d,
            other.c * self.a + other.d * self.c, other.c * self.b + other.d * self.d,
            other.a * self.e + other.b * self.f + other.e,
            other.c * self.e + other.d * self.f + other.f,
        )

    @property
    def scale_factor(self):
        return math.sqrt(abs(self.a * self.d - self.b * self.c))

    @staticmethod
    def translate(dx, dy):
        return Affine(e=dx, f=dy)

    @staticmethod
    def scale(k, cx=0.0, cy=0.0):
        return Affine(k, 0, 0, k, cx * (1 - k), cy * (1 - k))

    @staticmethod
    def rotate(angle, cx=0.0, cy=0.0):
        co, si = math.cos(angle), math.sin(angle)
        return Affine(co, -si, si, co, cx - co * cx + si * cy, cy - si * cx - co * cy)

    @staticmethod
    def mirror_x(cx):
        """Espejo respecto de la recta vertical ``x = cx``."""
        return Affine(-1, 0, 0, 1, 2 * cx, 0)

    @staticmethod
    def mirror_y(cy):
        """Espejo respecto de la recta horizontal ``y = cy``."""
        return Affine(1, 0, 0, -1, 0, 2 * cy)


def _segments(sweep):
    return max(3, math.ceil(CIRCLE_SEGMENTS * abs(sweep) / TAU))


def arc(cx, cy, r, a0, a1, segments=None) -> list[Point]:
    """Puntos de un arco de ``a0`` a ``a1`` (radianes), ambos extremos incluidos."""
    n = segments or _segments(a1 - a0)
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def circle_points(cx, cy, r, segments=CIRCLE_SEGMENTS) -> list[Point]:
    return arc(cx, cy, r, 0, TAU, segments)[:-1]




def star_polygon(cx, cy, r_out, r_in, n, rot=-math.pi / 2) -> list[Point]:
    pts = []
    for k in range(2 * n):
        r = r_out if k % 2 == 0 else r_in
        a = rot + math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def diamond(cx, cy, rx, ry=None) -> list[Point]:
    ry = rx if ry is None else ry
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def box(cx, cy, hw, hh=None) -> list[Point]:
    hh = hw if hh is None else hh
    return [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]




def lens(p, q, bulge, n=14) -> list[Point]:
    """Hoja de dos arcos entre ``p`` y ``q``; ``bulge`` es la flecha de cada arco."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    side_a, side_b = [], []
    for k in range(n + 1):
        t = k / n
        h = 4 * bulge * t * (1 - t)  # parábola: la flecha máxima queda en el centro
        bx, by = p[0] + dx * t, p[1] + dy * t
        side_a.append((bx + nx * h, by + ny * h))
        side_b.append((bx - nx * h, by - ny * h))
    return side_a + side_b[-2:0:-1]


def spiral(cx, cy, r0, r1, a0, turns, direction=1, n=None) -> list[Point]:
    """Espiral de Arquímedes de radio ``r0`` a ``r1`` que empieza en el ángulo ``a0``."""
    n = n or max(12, int(abs(turns) * 40))
    return [(cx + (r0 + (r1 - r0) * k / n) * math.cos(a0 + direction * TAU * turns * k / n),
             cy + (r0 + (r1 - r0) * k / n) * math.sin(a0 + direction * TAU * turns * k / n))
            for k in range(n + 1)]


def union_of_circles(circles, samples=360) -> list[Point]:
    """Contorno de la unión de círculos ``(cx, cy, r)`` que contienen el origen.

    Es una figura estrellada respecto del origen, así que basta el radio máximo de
    corte de cada rayo con cada círculo: ``t = u·c + sqrt(r² - |c|² + (u·c)²)``.
    """
    pts = []
    for k in range(samples):
        a = TAU * k / samples
        ux, uy = math.cos(a), math.sin(a)
        best = 0.0
        for cx, cy, r in circles:
            proj = ux * cx + uy * cy
            disc = r * r - (cx * cx + cy * cy) + proj * proj
            if disc >= 0:
                best = max(best, proj + math.sqrt(disc))
        pts.append((best * ux, best * uy))
    return pts




def rect_outline(rect: Rect, style="recto", radius=0.0) -> list[Point]:
    """Contorno de un rectángulo con esquinas ``recto``, ``redondo``, ``cortado`` o ``concavo``.

    Se recorre en sentido horario en pantalla; cada esquina aporta los puntos entre el
    final del lado anterior y el inicio del siguiente.
    """
    r = min(radius, rect.w / 2, rect.h / 2)
    if style == "recto" or r <= 0:
        return rect.corners()
    half = math.pi / 2
    # (esquina, sx, sy, ángulos del arco redondo, ángulos del arco cóncavo)
    corners = [
        ((rect.x0, rect.y0), 1, 1, (math.pi, 3 * half), (half, 0.0)),
        ((rect.x1, rect.y0), -1, 1, (-half, 0.0), (math.pi, half)),
        ((rect.x1, rect.y1), -1, -1, (0.0, half), (3 * half, math.pi)),
        ((rect.x0, rect.y1), 1, -1, (half, math.pi), (0.0, -half)),
    ]
    pts = []
    for (px, py), sx, sy, round_angles, concave_angles in corners:
        if style == "redondo":
            pts += arc(px + sx * r, py + sy * r, r, *round_angles)
        elif style == "concavo":
            pts += arc(px, py, r, *concave_angles)
        else:  # cortado
            vertical, horizontal = (px, py + sy * r), (px + sx * r, py)
            pts += [vertical, horizontal] if sx == sy else [horizontal, vertical]
    return pts
