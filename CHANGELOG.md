# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

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
