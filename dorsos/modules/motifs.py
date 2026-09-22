"""Motivos reutilizables (rosetas, estrellas, hojas, lises, cruces) que componen los módulos."""
import math

from ..geometry import TAU, box, circle_points, lens, star_polygon
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


def fleur_de_lis(x, y, r, color, dot=None):
    """Flor de lis de alto ``2r`` centrada en ``(x, y)``, con el pétalo central hacia arriba.

    Todas las piezas arrancan dentro de la franja central, que las ata: así la figura se lee
    entera también a tamaño grande y girada.
    """
    top, bottom = y + r * 0.16, y + r * 0.38          # franja central
    out = [poly(lens((x, y - r), (x, bottom), r * 0.3), fill=color)]
    for side in (-1, 1):
        # pétalo lateral: sube hacia fuera desde la franja
        out.append(poly(lens((x + side * r * 0.08, bottom), (x + side * r * 0.84, y - r * 0.42), r * 0.2),
                        fill=color))
        # remate: dos lóbulos que cuelgan de la franja
        out.append(poly(lens((x, top), (x + side * r * 0.5, y + r * 0.92), r * 0.12), fill=color))
    out.append(poly(box(x, (top + bottom) / 2, r * 0.46, (bottom - top) / 2), fill=color))
    if dot:
        out.append(circle(x, y - r * 0.3, r * 0.1, fill=dot))
    return out


def flared_cross(x, y, r, waist, tip):
    """Cruz paté: brazos que se ensanchan de ``waist`` en el centro a ``tip`` en la punta."""
    pts = []
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux                      # perpendicular al brazo
        nx, ny = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        pts.append((x + ux * r - px * tip, y + uy * r - py * tip))
        pts.append((x + ux * r + px * tip, y + uy * r + py * tip))
        pts.append((x + (ux + nx) * waist, y + (uy + ny) * waist))
    return pts
