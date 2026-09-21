"""Línea de órdenes: ``python -m dorsos {generate,sheet,presets,modules}``."""
import argparse
import json
import random
import sys
from pathlib import Path

from .compose import build_scene
from .config import DorsoConfig, merge, set_path
from .constants import DEFAULT_DPI, FORMATS, SLOTS
from .errors import ConfigError
from .presets import load_preset, preset_names
from .randomize import randomize
from .registry import get_module, kinds
from .render_png import render_png, save_png
from .render_svg import render_svg
from .sheet import contact_sheet

DEFAULT_OUT_DIR = "salida"


def add_config_args(p):
    g = p.add_argument_group("configuración")
    g.add_argument("--preset", help="nombre de preset (ver 'presets')")
    g.add_argument("--config", help="fichero JSON de configuración")
    g.add_argument("--format", choices=list(FORMATS), help="formato de carta")
    g.add_argument("--dpi", type=int, help=f"resolución (por defecto {DEFAULT_DPI})")
    g.add_argument("--seed", type=int, help="semilla reproducible")
    g.add_argument("--set", dest="sets", action="append", default=[], metavar="RUTA=VALOR",
                   help="fija un parámetro, p. ej. --set frame.kind=geometrico --set style.density=0.7 "
                        "--set 'frame.options={\"motif\":\"puntos\"}' (el valor es JSON o texto)")
    g.add_argument("--random", action="store_true", help="randomiza todo lo que no esté bloqueado")
    g.add_argument("--lock", nargs="+", default=[], metavar="RUTA",
                   help="parámetros que --random conserva: palette, frame, frame.kind, palette.background...")


def base_dict(args) -> tuple[dict, list[str]]:
    """Diccionario base (defaults + preset + JSON + overrides) y rutas fijadas con --set."""
    data = DorsoConfig().to_dict()
    if args.preset:
        data = merge(data, load_preset(args.preset))
    if args.config:
        data = merge(data, json.loads(Path(args.config).read_text(encoding="utf-8")))
    for key in ("format", "dpi", "seed"):
        if getattr(args, key) is not None:
            data[key] = getattr(args, key)
    paths = []
    for item in args.sets:
        path, sep, raw = item.partition("=")
        if not sep:
            raise ConfigError(f"--set espera RUTA=VALOR, no {item!r}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        set_path(data, path, value)
        paths.append(path)
    return data, paths


def configs_from_args(args, count: int) -> list[tuple[str, DorsoConfig]]:
    data, set_paths = base_dict(args)
    base = DorsoConfig.from_dict(data)
    first_seed = args.seed if args.seed is not None else (base.seed if not args.random else random.SystemRandom().randrange(10 ** 6))
    out = []
    for k in range(count):
        seed = first_seed + k
        if args.random:
            cfg = randomize(base, seed, [*args.lock, *set_paths])
        else:
            cfg = DorsoConfig.from_dict({**data, "seed": seed})
        out.append((args.preset or "dorso", cfg))
    return out


def cmd_generate(args):
    items = configs_from_args(args, args.count)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for label, cfg in items:
        stem = args.name or label
        if args.random or args.count > 1:
            stem = f"{stem}-{cfg.seed}"
        scene = build_scene(cfg)
        if "png" in args.formats:
            save_png(render_png(scene, cfg.dpi), out_dir / f"{stem}.png", cfg.dpi, scene.metadata)
        if "svg" in args.formats:
            (out_dir / f"{stem}.svg").write_text(render_svg(scene), encoding="utf-8")
        if args.save_config:
            cfg.save(out_dir / f"{stem}.json")
        print(out_dir / stem, f"(seed {cfg.seed})")


def cmd_sheet(args):
    if args.presets:
        items = [(name, DorsoConfig.from_dict(_with_overrides(args, load_preset(name)))) for name in preset_names()]
    else:
        items = [(f"seed {cfg.seed}", cfg) for _, cfg in configs_from_args(_as_random(args), args.count)]
    sheet = contact_sheet(items, args.cols, args.height)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(args.out, sheet.size)


def _as_random(args):
    args.random = True
    return args


def _with_overrides(args, preset):
    data = merge(DorsoConfig().to_dict(), preset)
    for key in ("format", "dpi", "seed"):
        if getattr(args, key) is not None:
            data[key] = getattr(args, key)
    return data


def cmd_presets(args):
    for name in preset_names():
        print(name)


def cmd_modules(args):
    for slot in args.slot or SLOTS:
        print(f"[{slot}]")
        for kind in kinds(slot):
            cls = get_module(slot, kind)
            print(f"  {kind}: {cls.doc}")
            for key, opt in cls.options.items():
                extra = list(opt.choices) if opt.choices else (f"{opt.lo}..{opt.hi}" if opt.lo is not None else "")
                print(f"      {key} = {opt.default!r}  {opt.doc} {extra}")


def build_parser():
    parser = argparse.ArgumentParser(prog="dorsos", description="Generador procedural de dorsos de cartas.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="genera dorsos en PNG y/o SVG")
    add_config_args(g)
    g.add_argument("-o", "--out", default=DEFAULT_OUT_DIR, help="directorio de salida")
    g.add_argument("--name", help="nombre base de los ficheros")
    g.add_argument("--formats", nargs="+", choices=("png", "svg"), default=["png", "svg"])
    g.add_argument("--count", type=int, default=1, help="cuántos dorsos (semillas consecutivas)")
    g.add_argument("--save-config", action="store_true", help="guarda también el JSON completo")
    g.set_defaults(func=cmd_generate)

    s = sub.add_parser("sheet", help="hoja de muestras en cuadrícula")
    add_config_args(s)
    s.add_argument("-o", "--out", default=f"{DEFAULT_OUT_DIR}/muestras.png")
    s.add_argument("--presets", action="store_true", help="todos los presets (si no, dorsos aleatorios)")
    s.add_argument("--count", type=int, default=12, help="dorsos aleatorios de la hoja")
    s.add_argument("--cols", type=int, default=6)
    s.add_argument("--height", type=int, default=420, help="alto en píxeles de cada carta")
    s.set_defaults(func=cmd_sheet)

    sub.add_parser("presets", help="lista los presets").set_defaults(func=cmd_presets)
    m = sub.add_parser("modules", help="lista módulos y sus opciones")
    m.add_argument("slot", nargs="*", choices=SLOTS)
    m.set_defaults(func=cmd_modules)
    return parser


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # la consola de Windows no es UTF-8 por defecto
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
