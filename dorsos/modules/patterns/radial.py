"""Patrón polar: el único que no tesela, sino que sale del centro de la carta."""
import math

from ...geometry import TAU, arc
from ...primitives import circle, line, poly
from ...registry import register
from ..base import Opt
from ..motifs import petals
from .base import Pattern


@register("pattern", "radial")
class Radial(Pattern):
    doc = "Polar, desde el centro de la carta: rayos, telaraña, anillos de muaré o un rosetón."
    options = {**Pattern.common,
               "cell_mm": Opt(4.0, "separación entre anillos", lo=1.0, hi=12.0, rand=False),
               "style": Opt("rayos", "variante", choices=("rayos", "telarana", "moare", "petalos")),
               "rays": Opt(24, "rayos, brazos o sectores", lo=8, hi=48, rlo=12, rhi=32)}

    def build(self, ctx):
        o = self.o
        f = ctx.field
        cx, cy = f.cx, f.cy
        # hasta la esquina más lejana: el recorte del marco se encarga del resto
        radius = math.hypot(max(cx - f.x0, f.x1 - cx), max(cy - f.y0, f.y1 - cy))
        # múltiplo de 4: así el espejo lleva sector par a sector par y el dibujo ya es simétrico
        n = max(4, 4 * round(o["rays"] / 4))
        step = o["cell_mm"] * ctx.scale
        ln, fl, dt = (ctx.color(o[k]) for k in ("line", "fill", "dot"))
        w = ctx.weight(o["weight"])
        style = o["style"]

        if style == "rayos":
            return self.wedges(cx, cy, radius, n, step, ln, fl, dt, w)
        if style == "petalos":
            return self.rosette(cx, cy, radius, n, ln, fl, dt, w)
        prims = self.rings(cx, cy, radius, step, ln, dt, w, dense=style == "moare")
        if style == "telarana":
            for k in range(n):
                a = TAU * k / n
                prims.append(line([(cx + step * 0.5 * math.cos(a), cy + step * 0.5 * math.sin(a)),
                                   (cx + radius * math.cos(a), cy + radius * math.sin(a))], ln, w))
            prims.append(circle(cx, cy, step * 0.4, fill=dt))
        return prims

    @staticmethod
    def wedges(cx, cy, radius, n, step, ln, fl, dt, w):
        """Sectores alternos rellenos, con anillos por encima."""
        prims = []
        for k in range(0, n, 2):
            a0, a1 = TAU * k / n, TAU * (k + 1) / n
            prims.append(poly([(cx, cy)] + arc(cx, cy, radius, a0, a1), fill=fl))
        for r in Radial.radii(radius, step * 2):
            prims.append(circle(cx, cy, r, stroke=ln, width=w))
        prims.append(circle(cx, cy, step * 0.6, fill=dt))
        return prims

    @staticmethod
    def rings(cx, cy, radius, step, ln, dt, w, dense):
        prims = []
        for i, r in enumerate(Radial.radii(radius, step / 2 if dense else step)):
            prims.append(circle(cx, cy, r, stroke=dt if dense and i % 3 == 0 else ln, width=w))
        return prims

    @staticmethod
    def rosette(cx, cy, radius, n, ln, fl, dt, w):
        """Un solo rosetón que ocupa la carta entera.

        Se descartó la espiral: el espejo invierte el sentido de giro, así que una espiral
        nunca sale simétrica. Los pétalos sí lo son.
        """
        prims = petals(cx, cy, radius * 0.08, radius, n, fl, ln, w, bulge=0.11)
        prims += petals(cx, cy, radius * 0.06, radius * 0.45, n // 2, None, ln, w * 0.8,
                        rot=-math.pi / 2 + math.pi / n, bulge=0.13)
        prims.append(circle(cx, cy, radius * 0.07, fill=dt, stroke=ln, width=w))
        return prims

    @staticmethod
    def radii(radius, step):
        return [step * k for k in range(1, max(2, int(radius / step)) + 1)]
