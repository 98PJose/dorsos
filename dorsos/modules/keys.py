"""Grecas: el trazado de cada llave sobre una rejilla de trazo y hueco iguales.

Cada llave se da como la línea central de un módulo en unidades de rejilla, de centro de
celda a centro de celda (``c + 0,5``). El último punto de un módulo es el primero del
siguiente, así que al encadenarlos la greca sale continua. Cada tramo se pinta como un
rectángulo de una unidad de grueso: las esquinas quedan en ángulo recto, como en la greca
clásica, en vez del redondeo que dejaría un trazo con uniones.

La banda completa lleva un raíl de una unidad arriba y otro abajo, separados de la llave
por un hueco de una unidad, así que mide ``height + 4`` unidades de alto.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Key:
    path: tuple        # línea central de un módulo, en unidades de rejilla
    period: int        # ancho del módulo: el desplazamiento hasta el siguiente
    height: int        # alto de la llave, sin raíles
    axis: float = 0.0  # recta vertical, dentro del módulo, respecto de la que es simétrico
    # Si la llave tiene un eje propio, se ancla ahí en el eje de la carta y el espejo global
    # la continúa sin costura. Una llave quiral (meandro, olas) no lo tiene: con 0 el eje de
    # la carta cae entre dos módulos y se ven dos llaves que se alejan del centro.

    @property
    def band_units(self) -> int:
        """Alto de la banda con sus dos raíles y los dos huecos."""
        return self.height + 4


KEYS = {
    # La greca clásica de doble espiral: entra por abajo, sube, da vuelta y media hacia
    # dentro y vuelve a salir por un pasillo paralelo hasta el módulo siguiente.
    "meandro": Key(((0.5, 8.5), (0.5, 0.5), (8.5, 0.5), (8.5, 6.5), (4.5, 6.5), (4.5, 4.5),
                    (6.5, 4.5), (6.5, 2.5), (2.5, 2.5), (2.5, 8.5), (10.5, 8.5)), 10, 9),
    # Llave de una sola vuelta, la onda corrida.
    "olas": Key(((0.5, 4.5), (0.5, 0.5), (4.5, 0.5), (4.5, 2.5), (2.5, 2.5), (2.5, 4.5),
                 (6.5, 4.5)), 6, 5),
    # Almenado: onda cuadrada de almenas y huecos iguales.
    "almenado": Key(((0.5, 4.5), (0.5, 0.5), (4.5, 0.5), (4.5, 4.5), (8.5, 4.5)), 8, 5, axis=2.5),
}


def key_rects(key: Key, x0: float, y0: float, ux: float, uy: float, modules: int) -> list[list]:
    """Rectángulos de ``modules`` módulos seguidos desde ``(x0, y0)``, con celdas de ``ux`` × ``uy``.

    ``(x0, y0)`` es la esquina superior izquierda de la llave, sin contar raíles.
    """
    rects = []
    for k in range(modules):
        ox = x0 + k * key.period * ux
        for (ax, ay), (bx, by) in zip(key.path, key.path[1:]):
            left, right = min(ax, bx) - 0.5, max(ax, bx) + 0.5
            top, bottom = min(ay, by) - 0.5, max(ay, by) + 0.5
            rects.append([(ox + left * ux, y0 + top * uy), (ox + right * ux, y0 + top * uy),
                          (ox + right * ux, y0 + bottom * uy), (ox + left * ux, y0 + bottom * uy)])
    return rects


def band_rects(key: Key, x0: float, y0: float, ux: float, uy: float, modules: int,
               rails: bool = True) -> list[list]:
    """La banda entera: raíl, hueco, llave, hueco y raíl, de ``modules`` módulos de largo."""
    rects = key_rects(key, x0, y0 + 2 * uy, ux, uy, modules)
    if rails:
        x1 = x0 + modules * key.period * ux
        bottom = y0 + key.band_units * uy
        rects.append([(x0, y0), (x1, y0), (x1, y0 + uy), (x0, y0 + uy)])
        rects.append([(x0, bottom - uy), (x1, bottom - uy), (x1, bottom), (x0, bottom)])
    return rects


def spiral_arm(X: int, Y: int) -> list[tuple[int, int]]:
    """Un brazo de la greca en espiral: línea central en unidades desde el centro.

    Empieza en la esquina superior izquierda ``(-X, -Y)`` y gira en sentido horario hacia
    dentro. Cada lado avanza cuatro unidades menos que el anterior del mismo sentido: dos de
    su propio trazo y hueco y dos que ocupa el otro brazo. Termina cuando un lado ya no
    avanzaría al menos dos unidades en su sentido, porque chocaría con el otro brazo.
    """
    pts = [(-X, -Y)]
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    for k in range(max(X, Y)):
        corners = ((X - 4 * k, -Y + 4 * k), (X - 4 * k, Y - 2 - 4 * k),
                   (-X + 2 + 4 * k, Y - 2 - 4 * k), (-X + 2 + 4 * k, -Y + 4 + 4 * k))
        for (dx, dy), (bx, by) in zip(directions, corners):
            ax, ay = pts[-1]
            if (bx - ax) * dx + (by - ay) * dy < 2:
                return pts
            pts.append((bx, by))
    return pts


def joins_through_centre(arm) -> bool:
    """El brazo acaba recorriendo el eje vertical: con el otro brazo forma una S por el centro."""
    return len(arm) > 1 and arm[-1][0] == 0 and arm[-2][0] == 0


def spiral_paths(X: int, Y: int) -> list[list[tuple[int, int]]]:
    """La espiral doble: el segundo brazo es el primero girado 180° respecto del centro.

    Si el primer brazo acaba recorriendo el eje vertical, el segundo lo recorre en sentido
    contrario: los dos últimos tramos se funden en una sola barra central y la espiral es
    un único trazo en S. Si no, quedan como dos brazos sueltos.
    """
    arm = spiral_arm(X, Y)
    other = [(-x, -y) for x, y in arm]
    if joins_through_centre(arm):
        return [arm[:-1] + other[::-1][1:]]
    return [arm, other]


def fitted_spiral(half_w: float, half_h: float) -> tuple[int, int]:
    """Semiancho y semialto, en unidades, de la espiral más grande que cabe y se une en S.

    Se prueban hasta tres unidades menos de ancho y una menos de alto: a cambio de ese
    margen, la espiral sale en un solo trazo.
    """
    X0, Y0 = int(half_w - 0.5), int(half_h - 0.5)
    for Y in (Y0, Y0 - 1):
        for X in range(X0, X0 - 4, -1):
            if X > 2 and joins_through_centre(spiral_arm(X, Y)):
                return X, Y
    return X0, Y0


def path_rects(path, cx: float, cy: float, ux: float, uy: float) -> list[list]:
    """Rectángulos de una línea central dada en unidades alrededor de ``(cx, cy)``."""
    rects = []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        left, right = cx + (min(ax, bx) - 0.5) * ux, cx + (max(ax, bx) + 0.5) * ux
        top, bottom = cy + (min(ay, by) - 0.5) * uy, cy + (max(ay, by) + 0.5) * uy
        rects.append([(left, top), (right, top), (right, bottom), (left, bottom)])
    return rects
