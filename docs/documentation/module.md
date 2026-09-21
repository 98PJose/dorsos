# Documentación por módulo

Referencia de cada fichero de `dorsos/`: qué hace, cómo se integra, entradas, salidas,
estructuras de datos, funciones y clases, dependencias y bucles relevantes. La lista
completa y actual de opciones de cada módulo ornamental sale de
`python -m dorsos modules [ranura]`, que se genera de las declaraciones `Opt` y no puede
quedar desfasada.

## Flujo de datos

```
JSON / preset / --set ──► DorsoConfig ──► build_scene ──► Scene ──► render_png ──► PNG
                                │              │                └─► render_svg ──► SVG
                        randomize (opcional)   └─ módulos (frame, pattern, medallion, corners)
```

`DorsoConfig` (datos) → `compose.build_scene` (instancia los módulos y les da un `Context`)
→ `Scene` (capas de primitivas + simetría) → renderizadores. Los módulos no conocen ni el
formato de salida ni la simetría global: solo devuelven primitivas en milímetros.

## Núcleo

### `constants.py`
Constantes sin lógica: `FORMATS` (`poker` 63×88, `espanola` 61,5×95), `DEFAULT_DPI=300`,
`SUPERSAMPLE=4` (par), `ROLES` (roles de color), `SLOTS`, `NO_MODULE="none"`,
`STYLE_LIMITS` (rango válido de cada parámetro de estilo), límites de dpi y de tamaño,
`CIRCLE_SEGMENTS=72`. Cualquier valor configurable nuevo va aquí, no en el código.

### `errors.py`
`ConfigError(ValueError)`: única excepción de validación. La CLI la traduce a
`error: …` y código de salida 1.

### `config.py`
- **Dataclasses** `Palette` (5 colores), `Style` (5 números), `Symmetry` (2 booleanos),
  `ModuleSpec` (`kind`, `enabled`, `options`; propiedad `active`), `DorsoConfig` (raíz).
- `DorsoConfig.to_dict(full)`/`from_dict`/`to_json`/`from_json`/`save`/`load`. `from_dict`
  mezcla el dict sobre los valores por defecto (así las configuraciones parciales valen),
  rechaza claves desconocidas y llama a `validate()`. `full=True` incluye los valores por
  defecto de las opciones de cada módulo (lo que guardan `--save-config` y los PNG/SVG).
- `DorsoConfig.size`: `(ancho, alto)` en mm; con `format="custom"` sale de `size_mm`.
- `validate()`: rangos de dpi, estilo y tamaño, colores, booleanos, existencia del módulo y
  validez de sus opciones (`Module.resolve_options`).
- Utilidades: `merge` (mezcla profunda; `options` se reemplaza entero), `get_path`,
  `set_path` (rutas con puntos como `frame.options.motif`).
- Depende de `constants`, `errors`, `modules.base.Opt` y, dentro de funciones, de `registry`.

### `registry.py`
`register(slot, name)` (decorador de clase), `kinds(slot)`, `get_module(slot, name)`.
Importan perezosamente el paquete `modules` para que los decoradores se ejecuten.
Estructura: `_REGISTRY[slot][name] -> clase`.

### `geometry.py`
- `Rect` (`x0,y0,x1,y1`; `w,h,cx,cy`, `inset`, `corners`).
- `Affine` (`a..f`, `__call__`, `then`, `scale_factor`; fábricas `translate`, `scale`,
  `rotate`, `mirror_x`, `mirror_y`).
- Contornos (devuelven listas de puntos): `arc`, `circle_points`, `star_polygon`, `diamond`,
  `box`, `lens`, `spiral`, `union_of_circles` (función radial de una unión de círculos),
  `rect_outline` (esquinas `recto`, `redondo`, `cortado`, `concavo`) y `diagonal_segment`
  (trozo de la recta `x ± y = c` dentro de un rectángulo).
- Sin dependencias salvo `constants.CIRCLE_SEGMENTS`.

### `primitives.py`
`Polygon`, `Polyline`, `Circle` (dataclasses inmutables con color hex y grosor en mm),
`Group(items, clip)` (capa con recorte poligonal opcional), constructores `poly`, `line`,
`circle`, y `transform`/`transform_all` (aplican una isometría). Un círculo transformado
conserva su forma porque solo se admiten isometrías y semejanzas.

### `scene.py`
`Scene(width, height, layers, bilateral, rotational_180, metadata)`.
`symmetry_plan()` devuelve el dominio fundamental (`Rect`) y, por cada isometría no
trivial, `(Affine, Rect imagen del dominio)`. Los tres casos: espejo, giro de 180° y
ambos (grupo de Klein). Ver `docs/methodology/model.tex`, sección 2.

### `compose.py`
`build_scene(cfg)`. Orden de capas: papel (rectángulo redondeado) → campo (fondo) →
patrón (recortado a `result.pattern_clip`) → marco → medallón → esquinas. El patrón va
antes que el marco, así que un marco con `bleed` se dibuja encima de él. Instancia cada
módulo activo con `get_module(slot, kind)(options)` y un `Context` con el campo que le
corresponde (`outer_rect` para el marco; `inner_rect` que devuelve el marco para el resto).
Si no hay marco, el campo es un rectángulo con radio `PLAIN_FIELD_RADIUS_MM`.

### `render_png.py`
- `pixel_size(scene, dpi)` → `(px, py)`.
- `render_png(scene, dpi, supersample)` → `PIL.Image` RGBA. Dibuja a `supersample`×, aplica
  la simetría con transposiciones exactas de imagen y reduce con filtro de caja
  (`Image.reduce`). El lienzo inicial es del color del papel con alfa 0 para que las
  esquinas transparentes no se oscurezcan al reducir.
- `save_png(img, path, dpi, metadata)`: guarda con `dpi` y la configuración en el chunk de
  texto `dorsos.config`.
- Bucle principal: por cada `Group`, dibuja sus primitivas; con recorte, copia el lienzo,
  dibuja y restaura fuera de la máscara. Trazos: `ImageDraw.line(joint="curve")` (uniones
  redondas, igual que el SVG) y círculos en los extremos de las polilíneas.

### `render_svg.py`
`render_svg(scene)` → texto SVG en mm (`width="63mm"`, `viewBox="0 0 63 88"`). Los recortes
son `<clipPath>` poligonales. La simetría se hace con un `<g id="dorso">` en `<defs>`, un
`<use>` sin recortar y un `<use>` con `matrix(a c b d e f)` recortado a cada imagen del
dominio. La configuración va en `<desc>`.

### `palettes.py`
`NAMED` (paletas de fondo/primario/secundario/acento), `random_palette(rng)` (campo
saturado oscuro y trazo claro el 80 %, invertido el resto; tonos limitados a `HUES`).

### `presets.py`
`preset_names()`, `load_preset(name)`: leen `dorsos/presets/*.json`, que son
configuraciones parciales (se mezclan sobre los valores por defecto).

### `randomize.py`
`randomize(base, seed, lock, layers)`. Genera paleta, estilo y, por ranura, un módulo (con
pesos en `KIND_WEIGHTS`) y sus opciones (`Module.random_options`); después copia de `base`
cada ruta de `lock`. `LAYERS` son las capas aleatorizables (`palette`, `style` y las cuatro
ranuras); `layers=None` las aleatoriza todas y, si se da una lista, las demás se añaden al
bloqueo, que es cómo `--random pattern` deja el resto intacto. No toca `format`, `dpi` ni
`symmetry`. Devuelve una `DorsoConfig` validada.

### `sheet.py`
`contact_sheet(items, cols, card_height_px)` → imagen con las cartas en cuadrícula y su
etiqueta. Renderiza cada carta con el dpi que da esa altura.

### `cli.py`
Subcomandos `generate`, `sheet`, `presets`, `modules`. `base_dict(args)` mezcla defecto →
preset → `--config` → `--format/--dpi/--seed` → `--set`. `configs_from_args` produce
`--count` configuraciones con semillas consecutivas; con `--random` las pasa por
`randomize` bloqueando `--lock` y las rutas dadas con `--set`. Errores de configuración →
`error: …` y código 1.

## Módulos ornamentales

Todos derivan de `modules/base.Module` y se registran con `@register(ranura, nombre)`.

### `modules/base.py`
- `Opt(default, doc, choices, lo, hi, color, rand, rlo, rhi)`: declara una opción. `check`
  valida y normaliza; `sample(rng)` produce un valor aleatorio dentro de `rlo..rhi`
  (subrango sensato para randomizar) o de `choices`.
- `Context`: `card`, `field`, `palette`, `density`, `scale`, `line_mm`, `seed`, `slot`;
  `color(ref)` (rol o hex), `weight(k)` (grosor en mm), `rng(*clave)` (generador
  independiente por módulo y clave).
- `Module`: `options` (dict de `Opt`), `resolve_options(given)` (valida y rellena defectos),
  `random_options(rng)`.
- `FrameResult(prims, outer, inner, inner_rect, pattern_area)`. `pattern_area` es un
  `(contorno, rectángulo)` opcional para el patrón; si es `None`, el patrón usa `inner`.
  Las propiedades `pattern_clip` y `pattern_rect` resuelven ese valor por defecto.

### `modules/motifs.py`
Piezas reutilizables: `petals`, `rosette`, `star`, `ring_of_dots`, `disc`.

### `modules/frames.py` — ranura `frame`
`Frame.build(ctx) -> FrameResult`. `LineFrame` (`simple`, `doble`): rectángulo(s)
concéntrico(s) con esquina `recto|redondo|cortado|concavo`. Su opción `bleed` devuelve un
`pattern_area` igual al campo entero: el patrón pasa por debajo de las líneas en vez de
recortarse al interior del marco. `BandFrame` (`geometrico`,
`ornamentado`): banda de ancho `band_mm` con un motivo repetido; cada lado se recorre en
coordenadas locales `(u, v)` y se lleva a la página con una rotación (`BandFrame.sides`).
Los motivos son métodos `motif_<nombre>(ctx, unidad, ancho)`; `corner_motif` dibuja los
bloques de esquina. Bucles: por lado, por unidad de motivo. `motif_arcos` es la arcada con
un anillo sobre cada arco y una lanza entre arcos.

### `modules/patterns/` — ranura `pattern`
- `base.py`: `Lattice(field, nominal, sub)` (retícula centrada: `pos`, `center`, `indices`),
  `StaggeredLattice(field, nominal, row_ratio)` (al tresbolillo: `cells()` da `(i, j, x, y)`),
  `fit_count`, `diagonal_constants` (rectas `x ± y = c` ancladas en el centro), `rows`
  (filas centradas) y `Pattern`, cuyo `build` recorre los índices y llama a
  `tile(ctx, lat, x, y, i, j, colors)`. Opciones comunes: `line`, `fill`, `dot`, `weight`,
  `variation`. `cell_colors` aplica `variation`, que invierte `line`/`fill` de una celda con
  esa probabilidad (generador por celda); los patrones que no usan `tile` lo llaman a mano.
- `geometric.py`: `rombos` (`concentricos`, `arlequin`, `cruzado`, `puntos`, más `macizo` y
  `estrellado`, que rellenan el rombo y dejan canales de fondo de anchura `gap` con un rombo
  menor en cada hueco), `celosia` y `reticula` (`cuadros`, `lineas`, `cruces`, `damero`;
  `inner`).
  `celosia` no usa `tile`: dibuja las rectas `x ± y = c` de lado a lado con `build`. Las
  constantes `c` se anclan en el centro de la carta (`line_constants`), de modo que el
  espejo intercambia las dos familias y deja el conjunto invariante; `geometry.diagonal_segment`
  recorta cada recta al campo.
- `floral.py`: `rosetas` (`roseta`, `estrella`, `anillos`, `mosaico`), `arabescos`
  (`volutas`, `ogivas`).
- `curved.py`: `ondas` (`circulos`, `escamas`, `sinuoso`), `guilloche` (`rosetones`, `haces`).
  `sinuoso` y `haces` no usan celdas: dibujan filas de curvas en todo el campo.
- `floral.py` incluye además `damasco` (mandorlas ojivales al tresbolillo, con `lens`) y
  `sembrado` (motivo suelto: flor de lis, trébol, cruz paté o lunares). El rombo que cierra
  el hueco del damasco va a un cuarto de celda a cada lado, que es donde están los huecos
  reales de una retícula al tresbolillo; a media celda la malla no sería simétrica.
- `tilings.py`: `panal` (hexágonos; `cubos` parte cada hexágono en tres rombos y los colorea
  como las caras de un cubo) y `mudejar` (estrellas de ocho puntas y octógonos).
- `bands.py`: `espiga` (barras a ±45°, chevrones o zigzag), `greca` (greca griega: módulos
  abiertos colgando de un raíl continuo, más el almenado, que es una onda cuadrada de una
  sola polilínea) y `entrelazo` (`cesteria` por celdas; `trenza` dibuja las dos familias de
  cintas diagonales y repinta un parche de la descendente en la mitad de los cruces, que es
  lo que produce el efecto de encima y debajo).
- `radial.py`: `radial`, el único polar. No tesela: sale del centro de la carta hasta la
  esquina más lejana. El número de sectores se redondea a múltiplo de cuatro para que el
  espejo lleve sector par a sector par. No hay variante de espiral: el espejo invierte el
  sentido de giro, así que una espiral no puede salir simétrica.

### `modules/medallions.py` — ranura `medallion`
`Medallion.build`: halo (despeja el patrón) → relleno → contornos concéntricos → perlas →
motivo interior (`roseta`, `estrella`, `rombo`, `circulo`, `flor`, `ninguno`). Cada forma
(`circulo`, `ovalo`, `rombo`, `roseta`, `cuatrilobulo`, `estrella`) implementa
`unit_outline()`; `aspect` estira en vertical.

### `modules/corners.py` — ranura `corners`
`Corners.build` dibuja el ornamento (`ornament`) para la esquina superior izquierda del
interior del marco y lo refleja a las otras tres. Formas: `cuarto_circulo`, `abanico`,
`roseta`, `rombos`, `hojas`. `clear` despeja un cuarto de disco de fondo bajo el ornamento.

## Cómo añadir un módulo

1. Crea una clase que herede de `Pattern` (o de `Frame`, `Medallion`, `Corners`, `Module`)
   con `options = {...}` y el método de dibujo.
2. Decórala con `@register("pattern", "mi_patron")`.
3. Impórtala desde `dorsos/modules/__init__.py` (o `patterns/__init__.py`).
4. Con eso ya funciona en JSON, `--set`, `modules`, la randomización (si añades su peso en
   `randomize.KIND_WEIGHTS`) y las pruebas parametrizadas de `tests/test_modules.py`.
