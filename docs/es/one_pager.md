---
layout: null
permalink: /es/one_pager.html
lang: es
---

<!--
  Spanish translation of docs/one_pager.md. Same content + structure;
  only the prose + the in-page labels are translated. The host
  /es/ prefix avoids breaking English search / nav. Future languages
  (zh, vi) follow the same pattern: /<lang>/<page>.html.

  Update procedure: when the English one_pager.md changes, update
  this file in the same commit. CI doesn't enforce parity (a
  contribution adding English content but not Spanish is fine;
  just file a follow-up issue for the translation).
-->

# Wattplot, Volante (Hoja Única para el Stand)

> **Una hoja 8.5×11, lista para imprimir.** Genera el PDF con
> `pandoc docs/one_pager.md -o one_pager_es.pdf` desde la raíz
> del repositorio.

## ¿Qué es?

Una cama de cultivo elevada (4×8 ft / 1.2×2.4 m) cuyo dosel es
un panel solar en funcionamiento. **La misma superficie cultivada
produce tomates *y* genera electricidad** — simbiosis entre
producción de energía y agricultura, no un compromiso.

## Diseñado para ser construido

| | **Básico** | **Inteligente** |
|---|---|---|
| Inclinación | Fija, puntal con perno (0/15/25/35°) | Motorizado, 0–35°, actuador lineal |
| Electrónica | Ninguna | Controlador ESP32 + sensores + PCB |
| Respuesta a tormenta | Manual: quitar perno, plegar (2 min) | Plegado automático por viento + manual |
| Panel | Panel recuperado / upcycled es ideal | Nuevo 620 W bifacial (o cualquier preset) |
| Costo | **~$400–650** (panel recuperado) | ~$1,600 |
| Tiempo | Un fin de semana | 10–15 hr + electrónica |
| Guía | [`docs/build_basic.md`](../build_basic.html) | [`docs/build_guide.md`](../build_guide.html) |

**Empieza por el Básico.** Es la idea completa en su forma más
barata: una cama elevada que da sombra al cultivo y te paga en
vatios, construida con taladro y sierra. El Inteligente es la
mejora — cada Básico tiene los agujeros para el puntal y la
línea de pivote listos para aceptar el actuador después.

## Números clave (Phoenix, AZ, Cat II 700-años, Exp C)

- **Viento:** ráfaga de diseño 115 mph a 3 seg. A 35° el panel
  en postes de 72" tiene un factor de seguridad (SF) de **2.55**
  contra el volteo. Estibado plano (0°) lleva el SF a 26.8 — la
  estiba es la respuesta a tormenta para ambos niveles.
- **Energía (inclinación 35°, Phoenix 2025):** 2,240 kWh/año.
  Estático 35° da 1,539 kWh/año; seguimiento azimutal 35° (techo
  teórico) llega a 2,240 kWh/año.
- **Rendimiento de tomates (inclinación 35°):** ~84 kg/año de
  4 plantas (unos 185 lb). La inclinación 90° "sol en la cama"
  da solo 52.7 kg con mucho más estrés térmico.
- **Costo (Inteligente):** ~$1,400 en partes, incluyendo
  panel, MPPT, microinversor, batería LiFePO4 12 V 100 Ah,
  PCB, sensor de suelo, luz de cultivo.
- **Madera:** todo corte de 90° sin inglete. 2×6 rieles de 8 ft
  (sin desperdicio), postes 4×4 de 72" (desperdicio de 24"),
  piel 1×6 entre postes (5 cursos = 27.5" de pared).
- **Eléctrico:** un panel (panel principal, ninguna panel auxiliar
  separada), un MPPT (Sunapex 10A para el Mini; Victron SmartSolar
  100/30 o EPEver Tracer 4210AN para tamaño completo), un
  microinversor (Enphase IQ7+ o APsystems DS3, 240 V, UL 1741).
- **Estructural:** 35° es el tope estructural (ver ADR-001). El
  límite está impuesto por el análisis de flexión de postes
  (4×4 sin refuerzo fallan a 35° → usar 6×6 o refuerzo
  lateral). La integración en vivo del análisis de postes está
  en `analysis/post_bending.py`.

## Cómo está conectado

```
┌──────────────────────────────────┐
│ Panel 620 W bifacial              │  ← única fuente solar
└────┬─────────────────────────────┘
     │ bus DC (30-40 V, 0-18 A)
     ├─► Microinversor (Enphase IQ7+) → 240 V CA → red
     │
     └─► MPPT (Victron 100/30 / EPEver 4210AN / Sunapex 10A)
            │
            ▼
        ┌──────────┐
        │ 12V      │
        │ LiFePO4  │  ← única batería
        └────┬─────┘
             │
             ▼
       ┌──────────────┐
       │ ESP32 + DRV8871 ├──► Actuador lineal (inclinación)
       │ BMI160 INA219  │
       │ DS18B20        │
       └────────────────┘
```

## El controlador inteligente (diseño objetivo)

**Cada prioridad tiene tope a θ_max = 35°** (ver
[`docs/control_law.md`](../control_law.html)). Las viejas modos
de 90° "secar" y "sol en la cama" están retiradas; para secar la
cama, estiba plana a 0° en su lugar, donde el panel no da
sombra y soporta ~cero carga de viento.

```
prioridad  fuente                              define θ deseado
─────────────────────────────────────────────────────────────
   1      anulación del usuario                0-35 arbitrario
   2      límite duro de corriente             θ = 0 (seguridad)
   3      NWS lluvia + suelo seco              θ = 0 (captar lluvia)
   4      NWS viento > 50 mph                 θ = 15 (preventivo)
   5      viento ≥ 50% I_safe                pausa seguimiento
   6      suelo húmedo 72h+                  θ = 0 (estibar, sol seca)
   7      suelo seco 48h+ sin lluvia → ahorrar θ = 35
   8      hora del día + modo seguimiento     θ = 0-35 (techo az.)
   L1     SOC batería < 50%                  luces apagadas
   L2     DLI natural > objetivo              luces apagadas
   L3     déficit DLI > 0                    luces encendidas
   L4     restricción dura                    8 hr mínimo oscuro
```

**Objetivo: mantener la corriente del motor por debajo de I_safe,
maximizando la inclinación comandada para exposición solar.** Ver
`docs/control_law.md` para la tabla canónica; el firmware
aplica el tope de 35° en `commanded_tilt` (no se puede comandar
> 35° desde ningún estado).

## Antes de construir

1. Lee [`docs/pre_build_checklist.md`](../pre_build_checklist.html)
   y revisa la madera. Nudos > 1" en la base de los postes 4×4
   son una señal para devolver la pieza a la tienda.
2. Lee la ADVERTENCIA grande en
   [`docs/disclaimers.html`](../disclaimers.html) — no es un
   producto certificado, no es reemplazo de un electricista, no
   es un juguete. El análisis de viento es de primer paso, no
   sellado por un PE.
3. Mira el [`ROADMAP.md`](../../ROADMAP.html) — el proyecto está
   en estado prototipo funcional; un build a tamaño completo
   necesita revisión de un ingeniero estructural.

## Demo en el stand

Los visitantes más comunes:

- "¿Cuánta energía genera?" → 2,240 kWh/año a 35° en Phoenix.
- "¿Cuánto cuesta?" → $400 (Básico) o $1,400 (Inteligente).
- "¿Por qué no es más empinado?" → 45° falla el análisis de
  viento; 35° es donde la energía y la estructura se encuentran.
- "¿De dónde sacaste el nombre?" → la planta Wattplot original
  (andrew welch, 2006) usa la capitalización "WattPlot"; este
  proyecto usa "Wattplot" en minúscula y les pedimos coexistencia.
  Ver [`docs/_internal/COEXISTENCE_REQUEST.md`](../_internal/COEXISTENCE_REQUEST.html).

## Lo que Wattplot **no** es

- **No es un producto llave en mano.** Sin diseño sellado por
  PE, sin inversor certificado UL, sin garantía. Tú lo
  construyes; tú cargas con el riesgo.
- **No es reemplazo de un electricista.** La cadena LiFePO4 /
  MPPT / microinversor debe instalarse según el código local.
- **No es un rastreador solar inteligente.** Inclinación de un
  solo eje con tope estructural a 35°, no un rastreador de doble
  eje.
- **No es reemplazo de un kit solar off-grid.** Sin
  monitorización de batería por app, sin soporte comercial.

## Documentos útiles

| Para | Lee |
|---|---|
| Construcción (Básico) | [`docs/build_basic.md`](../build_basic.html) |
| Construcción (Inteligente) | [`docs/build_guide.md`](../build_guide.html) |
| Cableado | [`docs/wiring.md`](../wiring.html) (STALE — ver pin map) |
| Pin map real | [`docs/pinmap.html`](../pinmap.html) |
| Esquemático | [`docs/schematic.html`](../schematic.html) |
| Control de firmware | [`docs/control_law.md`](../control_law.html) |
| Análisis de viento | [`analysis/wind_load_report.md`](../../analysis/wind_load_report.html) |
| Análisis de flexión de postes | [`analysis/post_bending_report.md`](../../analysis/post_bending_report.html) |
| Lista de corte | `python models/cut_list.py` |
| "Mi propio panel" | `python bring_your_own_panel.py --preset longi_620W` |

## Licencia

MIT. Eres libre de usar, modificar y vender productos basados
en este diseño. Atribución apreciada.

---

_Generado para el stand de Wattplot. Para erratas, abre un issue
en github.com/mokahlo/wattplot._
