"""Construye la escena de una configuración: papel, campo, patrón, marco, medallón y esquinas."""
from dataclasses import asdict

from .config import DorsoConfig
from .geometry import Rect, rect_outline
from .modules.base import Context, FrameResult
from .primitives import Group, poly
from .registry import get_module
from .scene import Scene

# Radio del campo cuando no hay marco que lo defina.
PLAIN_FIELD_RADIUS_MM = 0.8


def build_scene(cfg: DorsoConfig) -> Scene:
    width, height = cfg.size
    card = Rect(0, 0, width, height)
    style = cfg.style
    palette = asdict(cfg.palette)
    outer_rect = card.inset(style.margin_mm)

    def context(slot, field_rect):
        return Context(card, field_rect, palette, style.density, style.scale, style.line_width_mm, cfg.seed, slot)

    def module(slot):
        spec = cfg.slot(slot)
        return get_module(slot, spec.kind)(spec.options) if spec.active else None

    frame = module("frame")
    if frame:
        result = frame.build(context("frame", outer_rect))
    else:
        outline = rect_outline(outer_rect, "redondo", PLAIN_FIELD_RADIUS_MM)
        result = FrameResult([], outline, outline, outer_rect)
    inner_ctx = lambda slot: context(slot, result.inner_rect)  # noqa: E731

    paper = rect_outline(card, "redondo", style.corner_radius_mm)
    layers = [Group([poly(paper, fill=palette["paper"])]), Group([poly(result.outer, fill=palette["background"])])]
    pattern = module("pattern")
    if pattern:
        layers.append(Group(pattern.build(inner_ctx("pattern")), clip=tuple(result.inner)))
    layers.append(Group(result.prims))
    for slot in ("medallion", "corners"):
        mod = module(slot)
        if mod:
            layers.append(Group(mod.build(inner_ctx(slot))))

    return Scene(width, height, layers, cfg.symmetry.bilateral, cfg.symmetry.rotational_180, cfg.to_json(full=True))
