"""Motivos reutilizables (rosetas, estrellas, hojas) que componen los módulos."""
import math

from ..geometry import TAU, circle_points, lens, star_polygon
from ..primitives import circle, poly


def petals(cx, cy, r_in, r_out, n, fill, stroke, width, rot=-math.pi / 2, bulge=0.3):
    """``n`` pétalos en forma de hoja que salen del radio ``r_in`` al ``r_out``."""
    out = []
    for k in range(n):
        a = rot + TAU * k / n
        p = (cx + r_in * math.cos(a), cy + r_in * math.sin(a))
        q = (cx + r_out * math.cos(a), cy + r_out * math.sin(a))
        out.append(poly(lens(p, q, bulge * (r_out - r_in)), fill=fill, stroke=stroke, width=width))
    return out


def rosette(cx, cy, r, n, fill, stroke, width, dot=None, ring=None, rot=-math.pi / 2):
    """Roseta de ``n`` pétalos con botón central ``dot`` y aro exterior ``ring`` opcionales."""
    out = []
    if ring:
        out.append(circle(cx, cy, r, stroke=ring, width=width))
    out += petals(cx, cy, r * 0.12, r * 0.94, n, fill, stroke, width, rot)
    if dot:
        out.append(circle(cx, cy, r * 0.16, fill=dot))
    return out


def star(cx, cy, r, n, ratio, fill, stroke, width, rot=-math.pi / 2):
    return poly(star_polygon(cx, cy, r, r * ratio, n, rot), fill=fill, stroke=stroke, width=width)


def ring_of_dots(cx, cy, r, n, dot_r, fill, rot=-math.pi / 2):
    return [circle(cx + r * math.cos(rot + TAU * k / n), cy + r * math.sin(rot + TAU * k / n), dot_r, fill=fill)
            for k in range(n)]


def disc(cx, cy, r, fill=None, stroke=None, width=0.0):
    return poly(circle_points(cx, cy, r), fill=fill, stroke=stroke, width=width)
