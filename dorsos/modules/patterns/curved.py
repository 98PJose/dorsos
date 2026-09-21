"""Patrones de curvas: ondas (círculos, escamas, bandas sinuosas) y guilloché."""
import math

from ...geometry import TAU
from ...primitives import circle, line, poly
from ...registry import register
from ..base import Opt
from .base import Lattice, Pattern


@register("pattern", "ondas")
class Ondas(Pattern):
    doc = "Círculos solapados, escamas (seigaiha) o bandas sinuosas."
    options = {**Pattern.common,
               "cell_mm": Opt(6.0, "tamaño de cada motivo", lo=3.0, hi=16.0, rand=False),
               "style": Opt("circulos", "variante", choices=("circulos", "escamas", "sinuoso"))}

    @property
    def sub(self):
        return 2 if self.o["style"] == "escamas" else 1

    def indices(self, lat):
        if self.o["style"] == "escamas":
            return [(i, j) for i, j in lat.indices(pad=2) if (i + j) % 2 == 0]
        return lat.indices()

    def build(self, ctx):
        if self.o["style"] == "sinuoso":
            return self.bandas(ctx)
        return super().build(ctx)

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"])
        levels = self.levels(ctx)
        out = []
        if self.o["style"] == "circulos":
            r = s * math.sqrt(0.5)
            for k in range(levels):
                out.append(circle(x, y, r * (1 - 0.28 * k), stroke=ln, width=w))
            out.append(circle(x, y, s * 0.06, fill=dt))
        else:  # escamas: cada fila tapa la parte baja de la anterior
            r = s / 2
            out.append(circle(x, y, r, fill=fl, stroke=ln, width=w))
            for k in range(1, levels + 1):
                out.append(circle(x, y, r * (1 - k / (levels + 1)), stroke=ln, width=w * 0.8))
            out.append(circle(x, y, r * 0.12, fill=dt))
        return out

    def bandas(self, ctx):
        o = self.o
        ln, fl = ctx.color(o["line"]), ctx.color(o["fill"])
        lat = Lattice(ctx.field, o["cell_mm"] * ctx.scale)
        field, w = ctx.field, ctx.weight(o["weight"])
        period, amp = lat.s * 2, lat.s * 0.22
        n_pts = max(2, int(field.w / lat.s) * 12)
        xs = [field.x0 - period + (field.w + 2 * period) * k / n_pts for k in range(n_pts + 1)]
        row_step = lat.s / 2
        first = math.floor((field.y0 - field.cy) / row_step) - 2
        last = math.ceil((field.y1 - field.cy) / row_step) + 2
        curves = [[(x, field.cy + (r + 0.5) * row_step + amp * math.cos(TAU * (x - field.cx) / period)) for x in xs]
                  for r in range(first, last + 1)]
        prims = []
        for k in range(len(curves) - 1):
            if k % 2 == 0:
                prims.append(poly(curves[k] + curves[k + 1][::-1], fill=fl))
        prims += [line(c, ln, w) for c in curves]
        return prims


@register("pattern", "guilloche")
class Guilloche(Pattern):
    doc = "Guilloché: rosetones de curvas desfasadas o haces de sinusoides entrecruzados."
    options = {**Pattern.common,
               "cell_mm": Opt(11.0, "tamaño de cada motivo", lo=5.0, hi=26.0, rand=False),
               "style": Opt("rosetones", "variante", choices=("rosetones", "haces")),
               "lobes": Opt(8, "lóbulos de cada rosetón", lo=3, hi=16, rlo=6, rhi=12),
               "curves": Opt(10, "curvas por rosetón o por haz", lo=4, hi=24, rlo=8, rhi=14)}

    def build(self, ctx):
        if self.o["style"] == "haces":
            return self.haces(ctx)
        return super().build(ctx)

    def tile(self, ctx, lat, x, y, i, j, colors):
        ln, fl, dt = colors
        s, w = lat.s, ctx.weight(self.o["weight"]) * 0.7
        k, m = self.o["lobes"], self.o["curves"]
        out = []
        for ring, (radius, depth) in enumerate(((s * 0.47, 0.45), (s * 0.26, 0.5))):
            color = ln if ring == 0 else dt
            for c in range(m):
                phase = TAU * c / (m * k)
                pts = [(x + radius * (1 - depth * (0.5 + 0.5 * math.cos(k * (a - phase)))) * math.cos(a),
                        y + radius * (1 - depth * (0.5 + 0.5 * math.cos(k * (a - phase)))) * math.sin(a))
                       for a in (TAU * t / 180 for t in range(181))]
                out.append(line(pts, color, w))
        out.append(circle(x, y, s * 0.05, fill=fl))
        return out

    def haces(self, ctx):
        o = self.o
        ln, dt = ctx.color(o["line"]), ctx.color(o["dot"])
        lat = Lattice(ctx.field, o["cell_mm"] * ctx.scale)
        field, w = ctx.field, ctx.weight(o["weight"]) * 0.7
        period, amp = lat.s * 1.6, lat.s * 0.3
        n_pts = max(2, int(field.w / lat.s) * 16)
        xs = [field.x0 + field.w * k / n_pts for k in range(n_pts + 1)]
        m = o["curves"]
        prims = []
        for j in sorted({j for _, j in lat.indices(pad=1)}):
            yc = lat.y0 + (j + 0.5) * lat.step
            color = ln if j % 2 == 0 else dt
            for c in range(m):
                phase = math.pi * c / m
                prims.append(line([(x, yc + amp * math.cos(TAU * (x - field.cx) / period + phase)) for x in xs], color, w))
        return prims
