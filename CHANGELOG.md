# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

### Añadido

- Patrón **`celosia`**: rejilla de diagonales continuas de lado a lado, con variantes
  `simple`, `doble`, `puntos` y `rombos`.
- Variantes **`macizo`** y **`estrellado`** del patrón `rombos`: rombos rellenos (rectos o
  de lados cóncavos) separados por canales de fondo, con un rombo menor en cada hueco.
  La anchura del canal es la opción `gap`.
- Motivo **`arcos`** del marco `ornamentado`: arcada con un anillo sobre cada arco y una
  lanza entre arcos.
- Opción **`bleed`** de los marcos de línea: el patrón llena todo el campo y las líneas se
  dibujan encima, en vez de recortarse al interior del marco.
- **`--random` acepta capas**: `--random pattern`, `--random palette medallion`… Sin
  nombres sigue aleatorizando todas. En la API, `randomize(..., layers=[...])`.
- Cinco presets que reproducen dorsos comerciales clásicos: `marino-arcos`,
  `coral-celosia`, `pizarra-celosia`, `marino-mosaico` y `carmin-mosaico`.
- **Ocho patrones nuevos**, de 7 a 15, y de 25 a 51 variantes:
  - `panal`: teselado hexagonal (`simple`, `flor`, `cubos`, `estrellas`). `cubos` parte cada
    hexágono en tres rombos y los colorea como las caras de un cubo.
  - `mudejar`: lacería de estrellas de ocho puntas (`estrellas`, `lazo`, `octogonos`).
  - `espiga`: espiga de parqué, galón de chevrones y zigzag.
  - `greca`: greca griega (`meandro`, `olas`, `almenado`), en bandas continuas.
  - `entrelazo`: trenzado con efecto de encima y debajo (`cesteria`, `trenza`).
  - `damasco`: mandorlas ojivales al tresbolillo (`ojiva`, `flor`, `alternado`).
  - `sembrado`: motivo suelto sembrado (`flor_de_lis`, `trebol`, `cruz`, `lunares`).
  - `radial`: el único polar (`rayos`, `telarana`, `moare`, `petalos`).
- `StaggeredLattice`, retícula al tresbolillo centrada, y `regular_polygon`.
- Hoja `muestras/patterns.png` con todos los patrones y sus variantes en una cuadrícula
  roja.

## [0.1.0] - 2026-09-21

Primera versión del generador de dorsos.

### Añadido

- Configuración JSON (`DorsoConfig`) con validación estricta, formatos póker
  (63×88 mm) y española (61,5×95 mm), resolución configurable (300 ppp por defecto),
  paleta de cuatro colores más papel, estilo (densidad, escala, márgenes, grosor de
  línea, redondeo) y semilla.
- Módulos independientes y combinables: 4 marcos (`simple`, `doble`, `geometrico`,
  `ornamentado`), 6 patrones (`rombos`, `reticula`, `rosetas`, `ondas`, `arabescos`,
  `guilloche`) con 2 a 4 variantes cada uno, 6 medallones y 5 ornamentos de esquina.
- Simetría bilateral y de 180° aplicada sobre un dominio fundamental, exacta a nivel de
  píxel en PNG.
- Exportación PNG a tamaño físico (con `dpi` y configuración incrustada) y SVG en mm.
- 13 presets, randomización reproducible con parámetros bloqueables y hojas de muestras.
- CLI: `generate`, `sheet`, `presets` y `modules`.
- 312 pruebas, `docs/methodology/model.tex` y `docs/documentation/module.md`.
