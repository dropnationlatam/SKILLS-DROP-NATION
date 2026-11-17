---
tipo: proceso-motion
version: 2.0.0
actualizado: 2026-11-17
---

# Proceso de extracción de estilo v2 · aprender, clonar y superar

> [!info] PARA CLAUDE (no borrar)
> Con este proceso se convierte un grupo de mp4 de referencia en un **estilo reutilizable** que sale igual al original y luego **mejor**. Son 6 fases y ninguna se salta. Lo que se mide se escribe como **[medido]**, lo que se mira como **[visto]** y lo que cambiamos a propósito como **[mejora]**. Nunca se escribe una regla "a ojo" si se puede medir.

**Necesita:** las `Herramientas/` de la skill (`extraer_estilo.py`, `comparar.py`, `generar_sfx.py`), FFmpeg, Python con `opencv-python numpy scikit-learn pillow scenedetect` y, si se puede, `pytesseract` (y Tesseract con español) y `faster-whisper`. HyperFrames ya está instalado desde el Paso 1. Lo que falte se instala con permiso, como dice el Paso 1.
```bash
python3 -m pip install opencv-python numpy scikit-learn pillow scenedetect pytesseract faster-whisper
```
**Mínimo 3 referencias** del mismo estilo (con 1 sola se copian sus accidentes, no su estilo). Idealmente 4 o 5.

---

## Fase A · Medir todo lo medible (automático)

```bash
python3 "Herramientas/extraer_estilo.py" "Estilos/<Estilo>/Referencias" "Estilos/<Estilo>/Estudio"
```
Mide en cada referencia y en conjunto:
- **Ritmo:** cada corte con su tiempo, duración de cada plano, cortes por minuto, cortes en los primeros 3 s.
- **Transiciones:** clasifica cada corte (seco, fundido, barrido con desenfoque, destello, paso por negro).
- **Cámara por plano:** acercamiento o alejamiento en % por segundo, paneo en px/s, giro, sacudida y **qué easing** sigue (lineal, ease-out, ease-in, ease-in-out).
- **Color:** paleta en HEX con su %, por referencia y por plano; brillo, contraste, saturación y temperatura.
- **Composición:** mapa de dónde pasa la acción (arriba, centro o abajo) contra las zonas seguras.
- **Textos (OCR):** qué dice, dónde está (% de altura), tamaño de letra en px a 1920, color de relleno y de borde, cuánto dura en pantalla, palabras por bloque, mayúsculas.
- **Sonido:** volumen (LUFS), golpes o efectos por minuto, % de cortes con golpe, si hay música de fondo, % de silencio.
- **Voz (si hay faster-whisper):** transcripción con tiempos por palabra, palabras por segundo, a qué segundo suena la primera palabra y el gancho exacto de los primeros 3 s.

También deja para mirar: `planos.jpg` (un cuadro por plano), `gancho.jpg` (los primeros 3 s a 10 cuadros por segundo), `transiciones/NN.jpg` (8 cuadros alrededor de cada corte), `planos/NNN.jpg` (cuadros en tamaño completo) y `mapa_actividad.jpg`.

**Refuerzo con HyperFrames** cuando haga falta más precisión en algo puntual:
```bash
npx hyperframes measure events "<ref.mp4>" --map --json        # todo lo que aparece, cambia o desaparece + el sonido
npx hyperframes measure frames "<ref.mp4>" --range 4.6,5.4      # cuadros seguidos de un tramo
npx hyperframes measure curve  "<ref.mp4>" --from 1 --to 2      # easing exacto de un elemento que se mueve
npx hyperframes measure ink    "<ref.mp4>" --at 4.8 --roi 0,150,720,200   # tamaño real del texto
```

## Fase B · Leer cuadro a cuadro (Claude mira)

Abre **todas** las hojas: primero `planos.jpg` de cada referencia, luego `gancho.jpg`, luego **cada** tira de `transiciones/` y, para el detalle, los `planos/NNN.jpg` grandes. Llena esta ficha en `Estudio/Lectura.md`:

1. **Medio de dibujo:** ¿ilustración vectorial plana, semirrealista con degradados, 3D, recortes de foto, línea? ¿Con contorno o sin él? ¿De dónde viene la luz? ¿Qué textura tiene?
2. **Tipografía exacta:** familia (compárala con las fuentes que trae HyperFrames: Poppins, Montserrat, Inter, Outfit, Nunito, Oswald…), peso, tamaño a 1080 de ancho, interletrado, sombra o borde.
3. **Subtítulos:** cómo entra cada palabra (aparece, sube, escala, se escribe), qué pasa con las ya dichas, cuántas palabras por bloque, cuándo se corta el bloque, cómo se marca la palabra importante.
4. **Catálogo de recursos:** cada recurso que aparece, con su **tiempo**, cuánto dura y cómo se mueve. Cruza con `Recursos base.md`.
5. **Estructura del guion:** de qué tipo es el gancho, cuándo llega la revelación, dónde entra la metáfora y cómo cierra. Usa la transcripción si la hay.
6. **Mapa de sonido:** qué efecto suena en qué evento (cruza `golpes_t` de `datos.json` con los cortes y los pop-ups).
7. **Lo que no se repite:** detalles de una sola referencia. Eso no es estilo y no va a la guía.

## Fase C · Desarmar en recetas

Cada recurso de la ficha se convierte en una **receta** que HyperFrames pueda reproducir: nombre, cuándo usarla, duración, easing, valores y cómo se arma en HTML/CSS/SVG. Si ya existe en `plantilla/assets/estilo.js` de otro estilo, reúsala y cambia solo los valores. Si no existe, escríbela como función nueva (`EI.<nombre>`), sin `Math.random()` (usa `EI.azar(semilla)`), y con todo en función del tiempo del timeline.

Los números van a `estilo.json` (ritmo, cámara, transiciones, color, subtítulos, recursos, sonido, voz, guion), con lo **[medido]** separado de lo **[mejora]**.

## Fase D · Prueba de clon (demostrar que sale igual)

1. Elige **3 tramos** de una referencia: el **gancho** (0-3 s), un plano **por dentro** o el recurso más característico, y **una transición**.
2. Rehazlos en HyperFrames con las recetas (copia `plantilla/` de otro estilo o crea una con `npx hyperframes init`). Lo orgánico que no se pueda dibujar por código se arma con la imagen del producto o con una ilustración base de Canva con el prompt de la guía.
3. Renderiza y compara:
```bash
python3 "Herramientas/comparar.py" "<ref.mp4>" "clon.mp4" "Estudio/Clon"
npx hyperframes snapshot --at 0.5,1.5,2.5 --against "<ref.mp4>"     # lado a lado exacto
```
4. Corrige lo que falle (color, tamaño, tiempo, easing) y compara otra vez. **Máximo 2 vueltas.** Anota en la guía lo que quedó aproximado (por ejemplo, una fuente reemplazada).
5. El clon que pasa se convierte en la `plantilla/` del estilo.

## Fase E · Superar al original

Pasa el original por esta tabla de retención. Cada regla que el original **no** cumple se convierte en una **[mejora]** de la guía, activada por defecto:

| Regla de retención | Cómo se mide |
|---|---|
| Algo se transforma en pantalla antes de 0,8 s | `gancho.jpg` |
| Primer cambio de escena antes de 4 s | `primer_corte_s` |
| Plano de 2 a 4,5 s, o un evento visual cada ≤2 s | `plano_mediana_s` + lectura |
| Subtítulos de ≥64 px a 1080 de ancho y dentro del 80 % | OCR `alto_px_1920` |
| Nada importante en el 12 % de abajo (interfaz de la app) | `mapa_actividad.jpg` |
| Golpe de sonido en ≥80 % de los cortes | `cortes_con_golpe_pct` |
| Una palabra clave marcada por frase, y siempre la que lleva el sentido | lectura |
| El producto aparece como solución dentro de la lógica del video | guion |
| Cierre con acción (oferta o comentar) y final en bucle | lectura |

Además, mejora lo que el original hace a medias (por ejemplo: si usa la caja de palabra clave al azar, nosotros la usamos siempre en la palabra fuerte). Nunca "mejores" lo que es la identidad del estilo (paleta, medio de dibujo, tipo de subtítulo).

## Fase F · Empaquetar e importar

La carpeta del estilo queda así (es la misma que se sube al GitHub):
```
Estilos/<Nombre>/
├── Guía de estilo.md     (reglas con [medido] / [visto] / [mejora])
├── estilo.json           (todos los números)
├── plantilla/            (proyecto HyperFrames listo para copiar: index.html + assets/)
├── ejemplo/demo.mp4      (render de la plantilla)
├── Estudio/              (Informe de extracción.md, Lectura.md, hojas de cada referencia)
└── Referencias/          (los mp4 originales)
```
Paolo lo sube a `estilos-motion/<id>/` del repo y suma la línea en `estilos-motion/indice.json`. El alumno lo trae en un paso con `importar_estilo.py`.

**Mejora continua:** cada video aprobado puede subir la versión del estilo (`version` en `estilo.json` + línea en el historial de la guía).
