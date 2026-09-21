"""Paletas limitadas (fondo, primario, secundario, acento, papel): nombradas y aleatorias."""
import colorsys
import random

CREAM = "#f6f0e2"
WHITE = "#ffffff"

NAMED = {
    "rojo":     {"background": "#c8102e", "primary": WHITE, "secondary": "#8a0b20", "accent": "#f2c14e"},
    "coral":    {"background": "#e8546a", "primary": WHITE, "secondary": "#b32a45", "accent": "#2b2b3a"},
    "verde":    {"background": "#0f8a55", "primary": WHITE, "secondary": "#0a5c39", "accent": "#d9e8a0"},
    "azul":     {"background": "#1f4fa3", "primary": WHITE, "secondary": "#14346f", "accent": "#9ec3ff"},
    "marino":   {"background": "#1b2a5c", "primary": "#dfe6ff", "secondary": "#0d1638", "accent": "#7f90d6"},
    "celeste":  {"background": "#2aa4dc", "primary": WHITE, "secondary": "#1876a8", "accent": "#0b3f66"},
    "amarillo": {"background": "#f2b705", "primary": WHITE, "secondary": "#b98700", "accent": "#3a2d5e"},
    "violeta":  {"background": "#7d4fc9", "primary": "#f0e8ff", "secondary": "#523092", "accent": "#e6c94a"},
    "granate":  {"background": "#7a1230", "primary": CREAM, "secondary": "#4d0a1e", "accent": "#d4a94a"},
    "negro-oro": {"background": "#14141a", "primary": "#d4a94a", "secondary": "#3a3320", "accent": "#f4e3a8"},
    "crema-rojo": {"background": CREAM, "primary": "#b3122d", "secondary": "#e9b9b2", "accent": "#1f2a44"},
    "crema-azul": {"background": CREAM, "primary": "#1f3f8f", "secondary": "#b9c6e6", "accent": "#b3122d"},
}


# Tonos que dan colores de baraja (rojos, verdes, azules, morados); se evitan los amarillos
# y naranjas oscuros porque a esa luminosidad quedan enfangados (verde oliva, marrón).
HUES = (0.0, 0.03, 0.36, 0.42, 0.50, 0.56, 0.60, 0.65, 0.74, 0.80, 0.90, 0.95)


def _hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, min(max(l, 0), 1), min(max(s, 0), 1))
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def random_palette(rng: random.Random) -> dict:
    """Paleta clásica: campo saturado, trazo casi blanco, un tono oscuro y un acento.

    El 80 % de las veces el campo es oscuro y el trazo claro; el resto se invierte.
    """
    hue = rng.choice(HUES) + rng.uniform(-0.02, 0.02)
    saturation = rng.uniform(0.55, 0.85)
    accent_hue = hue + rng.choice((0.0, 0.5, 0.08, -0.08))
    if rng.random() < 0.8:
        return {
            "background": _hex(hue, saturation, rng.uniform(0.28, 0.42)),
            "primary": rng.choice((WHITE, CREAM, _hex(hue, 0.6, 0.92))),
            "secondary": _hex(hue, saturation, rng.uniform(0.16, 0.25)),
            "accent": _hex(accent_hue, rng.uniform(0.6, 0.9), rng.uniform(0.5, 0.65)),
            "paper": rng.choice((WHITE, CREAM)),
        }
    return {
        "background": rng.choice((CREAM, WHITE)),
        "primary": _hex(hue, saturation, rng.uniform(0.25, 0.38)),
        "secondary": _hex(hue, rng.uniform(0.35, 0.6), rng.uniform(0.78, 0.88)),
        "accent": _hex(accent_hue, rng.uniform(0.6, 0.9), rng.uniform(0.3, 0.45)),
        "paper": rng.choice((WHITE, CREAM)),
    }
