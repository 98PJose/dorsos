"""Constantes compartidas: formatos, límites de parámetros y valores por defecto."""

CONFIG_VERSION = 1

MM_PER_INCH = 25.4
DEFAULT_DPI = 300
MIN_DPI, MAX_DPI = 30, 1200
# Se dibuja a SUPERSAMPLE x y se reduce. Debe ser par: la simetría se aplica sobre el
# lienzo sobredimensionado y así el eje cae siempre entre dos píxeles.
SUPERSAMPLE = 4

# Formatos físicos (ancho, alto) en mm.
FORMATS = {
    "poker": (63.0, 88.0),
    "espanola": (61.5, 95.0),
}
CUSTOM_FORMAT = "custom"
MIN_SIZE_MM, MAX_SIZE_MM = 30.0, 200.0

# Roles de color que pueden usar los módulos en lugar de un hex literal.
ROLES = ("background", "primary", "secondary", "accent", "paper")

SLOTS = ("frame", "pattern", "medallion", "corners")
NO_MODULE = "none"

# Límites de los parámetros globales de estilo: nombre -> (mínimo, máximo).
STYLE_LIMITS = {
    "density": (0.0, 1.0),
    "scale": (0.4, 3.0),
    "margin_mm": (0.0, 10.0),
    "line_width_mm": (0.05, 1.5),
    "corner_radius_mm": (0.0, 8.0),
}

# Segmentos con los que se aproxima una circunferencia completa (se reparten en arcos).
CIRCLE_SEGMENTS = 72
