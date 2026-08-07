---
layout: null
permalink: /es/faq.html
lang: es
---

<!-- Spanish translation of docs/faq.md. -->

# Wattplot — Preguntas Frecuentes (Stand del Maker Faire)

Las respuestas están diseñadas para decirse en voz alta, no solo
leerse. Si una pregunta te toma por sorpresa en el stand, la
respuesta está aquí.

## Lo básico

### ¿Qué es?

Una cama de cultivo elevada (1.2×2.4 m / 4×8 ft) cuyo dosel es un
panel solar en funcionamiento. **La misma superficie cultivada
produce tomates *y* genera electricidad** — simbiosis entre
producción de energía y agricultura.

### ¿Cuánta energía genera?

En Phoenix, el de tamaño completo genera unos **2,240 kWh/año**
a 35° con un panel nuevo bifacial de 620 W, o **~850 kWh/año**
con un panel residencial recuperado típico. La simulación
completa en `analysis/sun_simulator.py` usa pvlib con datos
meteorológicos TMY de Phoenix y 5 horarios de inclinación. A
35° estático: 1,539 kWh/año. A 35° con seguimiento azimutal:
2,240 kWh/año (techo teórico; el firmware actual no implementa
seguimiento). El Mini v2.4 (panel ECO-WORTHY de 10 W) produce
~16 kWh/año, suficiente para alimentar el controlador y la luz de
cultivo.

### ¿Cuánto cuesta?

| Nivel | Costo | Tiempo | ¿Qué obtienes? |
|---|---|---|---|
| **Básico** | ~$400–650 | Un fin de semana | Cama + panel recuperado + puntal fijo |
| **Inteligente** | ~$1,400 | 10–15 h | Lo anterior + actuador, MPPT, microinversor, controlador, batería |

La cama en sí es ~$185 en madera (1×6 piel, 2×4 montantes,
2×6 tapas), ~$160 en tierra, ~$60 en postes. La electrónica del
Inteligente añade ~$700 más. Un salvamento de panel reduce el
costo del Básico en otros $50–100.

### ¿Cuánto pesa el agua que cosecha?

Ninguna — no cosechamos agua. La cama es de fondo abierto sobre
el suelo nativo, con drenaje por gravedad. El panel **reduce**
la evaporación del suelo al filtrar la luz solar directa de la
tarde.

## Diseño y construcción

### ¿Por qué 35° en vez de 90°?

90° vertical ("sol en la cama") falla el análisis de viento. A
35° el SF contra volteo es 2.55 (cima), pero a 45° cae a 1.89, a
50° a 1.69, y a 90° a 1.26. El poste 4×4 sin refuerzo también
falla a 35° (SF 0.65 vs objetivo 1.5, peor caso). Ver
[`analysis/post_bending_report.md`](../../analysis/post_bending_report.html).
Hay dos remedios: postes 6×6 (SF 2.53, pasa con margen) o
refuerzo lateral con corte a 90° (ángulo estructural o placa
de unión). Ambos siguen la regla de diseño #1 — sin ingletes.

### ¿Por qué una cama elevada y no un campo plano?

Dos razones. (1) La cama elevada expone el cultivo a la
temperatura ideal del suelo a 6" de profundidad; un campo plano
en Phoenix tiene 35 °C+ en la superficie. (2) Los 27.5" de
tierra (5 cursos de 1×6) pesan 4,500 lb y se convierten en el
lastre del que depende el diseño contra viento. Sin cama,
necesitarías un ancla de tierra — más caro, más feo, y peor
para las raíces.

### ¿Por qué 4×4 postes, no 6×6?

Es más barato, más fácil de encontrar, y suficiente si el panel
se mantiene a 35° o menos y se añade refuerzo lateral. Con 4×4
+ refuerzo el SF del poste cumple el objetivo. Sin refuerzo,
4×4 falla a 35° — el operador tiene que elegir entre (a)
upsize a 6×6 (SF 2.53, pasa con margen), o (b) añadir refuerzo
lateral con corte a 90° (placas de unión o ángulo estructural).
La regla de diseño #1 es "sin ingletes" — incluso el refuerzo
necesita ser a 90°.

### ¿La madera debe ser tratada a presión?

Sí — los montantes y durmientes están en contacto con el suelo
y la tierra húmeda. Use ACQ (no CCA, prohibido para uso
residencial desde 2003) con clasificación UC3B o UC4A ("contacto
con el suelo"). La piel 1×6 puede ser cedro (durabilidad
natural) o 1×6 PT si no te importa el contacto. La tabla
[`docs/pre_build_checklist.md`](../pre_build_checklist.html) tiene
la lista de compras.

### ¿Necesito un electricista?

Sí, para conectar el microinversor a la red. La cama en sí, la
batería, el MPPT, el controlador — todo eso es trabajo de
electricista de 12 V CC y se puede hacer con un multímetro y un
poco de cuidado. La parte de 240 V CA requiere un electricista
certificado, o al menos un permiso y una inspección. La ley de
[interconexión de Utah SB 190](https://le.utah.gov/~2024/bills/sbillint/SB0190.html)
(800 W sin permiso) y [California AB 1076](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202120220AB1076)
(5 kW sin permiso) regulan la conexión a la red.

## Operación

### ¿Cómo sabe cuándo doblarse?

El firmware lee el sensor de corriente IPROPI del DRV8871 cada
100 ms. Cuando el panel llega a un tope mecánico, el motor se
atasca, la corriente salta de ~0.3 A (libre) a 1.15+ A
(límite interno del DRV8871), IPROPI detecta el pico, y el
firmware declara fin de recorrido. Ver ADR-003.

### ¿Y si el firmware se cuelga?

El monitor TPL5110 propuesto (ADR-004) lo reiniciaría cada 30 s
si la señal de "todo OK" no llega. No implementado todavía en
v3.2 — es una mejora planeada para rev C del PCB.

### ¿Cuánta agua necesitan los tomates?

En Phoenix en verano, ~2 galones por día para 4 plantas. El
firmware riega automáticamente con el sensor de humedad del suelo
(vía un solenoid 12V que es accionado por el segundo DRV8871
en v3.2).

### ¿Qué pasa en una tormenta de viento?

El firmware dobla a 0° (estibado) si la corriente del motor
excede I_safe + 0.3 A (fuerza mecánica anormal, indicador de
viento alto) o si nFAULT persiste > 2 s. La comunicación con
el NWS para pronóstico de viento está en el código pero
todavía no es leída por el bucle de control; el umbral NWS
llega en un próximo firmware.

### ¿Necesito Wi-Fi?

Sí para la telemetría. El ESPHome firmware habla Home
Assistant vía la API nativa; el panel de control local habla la
API vía aiohttp. Sin Wi-Fi, el controlador sigue ejecutando
localmente, pero no ves los datos en el teléfono.

## El nombre

### ¿"Wattplot" entra en conflicto con wattplot.com?

Sí. WattPlot.com (Andrew Welch, desde 2006) es software de
monitorización solar. Usamos "Wattplot" en minúscula; les
pedimos coexistencia por correo. Si declinan, tenemos un
`RENAME_PLAN.md` listo con el plan de ejecución. Ver
[`docs/_internal/COEXISTENCE_REQUEST.md`](../_internal/COEXISTENCE_REQUEST.html).

### ¿Por qué no llamarlo "Solar Garden" o algo?

Queríamos un nombre que indicara la integración de las dos
funciones (energía + agricultura). "Wattplot" — Watt + plot —
dice exactamente eso. La integración en sí (energía y comida de
la misma superficie) es la innovación, no la electrónica.

## Comercial / legal

### ¿Puedo vender unidades?

Sí, bajo la licencia MIT, con tu propio cumplimiento. Pero:
- UL 1741 / IEEE 1547 para el microinversor
- NDS / PE-sellado para la estructura
- Cumplimiento NEC 690.31 para la instalación PV
- Cumplimiento local de zonificación
El proyecto no certifica nada de esto. Comprar y vender sin
cumplimiento es tu responsabilidad.

### ¿Tiene garantía?

No. Ver [`docs/disclaimers.html`](../disclaimers.html) §6.

### ¿Cómo contacto al mantenedor?

Abre un issue en github.com/mokahlo/wattplot, o envía un
correo a mokahlou@gmail.com.

## Para más información

- [README principal](../../README.html)
- [ROADMAP](../../ROADMAP.html) — qué está construido, qué falta
- [CHANGELOG](../../CHANGELOG.html) — qué cambió y cuándo
- [analysis/](../../analysis/) — los cálculos
