"""Escena: capas de primitivas más la simetría global que aplican los renderizadores.

La simetría no se construye en cada módulo: se dibuja la carta entera y después se
conserva solo un dominio fundamental, que se replica con las isometrías del grupo.

  * bilateral                 -> dominio: mitad izquierda,   isometría: espejo vertical
  * giro de 180°              -> dominio: mitad superior,    isometría: giro de 180°
  * ambas (grupo de Klein)    -> dominio: cuadrante superior izquierdo, tres isometrías
"""
from dataclasses import dataclass, field

from .geometry import Affine, Rect
from .primitives import bounds


@dataclass
class Scene:
    width: float
    height: float
    layers: list = field(default_factory=list)
    bilateral: bool = False
    rotational_180: bool = False
    metadata: str = ""  # JSON de la configuración, se incrusta en PNG y SVG

    def symmetry_plan(self) -> tuple[Rect, list[tuple[Affine, Rect]]]:
        """Devuelve el dominio fundamental y, por cada isometría, su imagen del dominio."""
        w, h = self.width, self.height
        cx, cy = w / 2, h / 2
        domain = Rect(0, 0, cx if self.bilateral else w, cy if self.rotational_180 else h)
        maps = []
        if self.bilateral:
            maps.append(Affine.mirror_x(cx))
        if self.rotational_180:
            maps.append(Affine.rotate(3.141592653589793, cx, cy))
        if self.bilateral and self.rotational_180:
            maps.append(Affine.mirror_y(cy))
        plan = []
        for aff in maps:
            x0, y0, x1, y1 = bounds([aff(p) for p in domain.corners()])
            plan.append((aff, Rect(x0, y0, x1, y1)))
        return domain, plan
