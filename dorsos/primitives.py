"""Primitivas vectoriales que consumen los renderizadores (PNG y SVG).

Las medidas están en mm y los colores son cadenas ``#rrggbb``. Los módulos solo
producen primitivas; nunca dibujan directamente.
"""
from dataclasses import dataclass, field

from .geometry import Affine, Point


@dataclass(frozen=True)
class Polygon:
    points: tuple
    fill: str | None = None
    stroke: str | None = None
    width: float = 0.0


@dataclass(frozen=True)
class Polyline:
    points: tuple
    stroke: str
    width: float


@dataclass(frozen=True)
class Circle:
    cx: float
    cy: float
    r: float
    fill: str | None = None
    stroke: str | None = None
    width: float = 0.0


@dataclass
class Group:
    """Primitivas dibujadas en orden y recortadas opcionalmente por un polígono."""
    items: list = field(default_factory=list)
    clip: tuple | None = None


def poly(points, fill=None, stroke=None, width=0.0) -> Polygon:
    return Polygon(tuple(points), fill, stroke, width)


def line(points, stroke, width) -> Polyline:
    return Polyline(tuple(points), stroke, width)


def circle(cx, cy, r, fill=None, stroke=None, width=0.0) -> Circle:
    return Circle(cx, cy, r, fill, stroke, width)


def transform(prim, aff: Affine):
    """Aplica una isometría (o semejanza) a una primitiva."""
    if isinstance(prim, Circle):
        cx, cy = aff((prim.cx, prim.cy))
        return Circle(cx, cy, prim.r * aff.scale_factor, prim.fill, prim.stroke, prim.width)
    pts = tuple(aff(p) for p in prim.points)
    if isinstance(prim, Polygon):
        return Polygon(pts, prim.fill, prim.stroke, prim.width)
    return Polyline(pts, prim.stroke, prim.width)


def transform_all(prims, aff: Affine) -> list:
    return [transform(p, aff) for p in prims]


def bounds(points: list[Point]):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)
