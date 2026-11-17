---
name: "edicion-anuncios-drop-nation"
description: "Hace los anuncios de un producto de Drop Nation de principio a fin: escribe de 3 a 5 guiones de hasta 30 segundos con metodologías probadas y, en Claude Code, arma el video vertical con los crudos, la voz por partes, subtítulos y textos de venta."
---

# Anuncios Drop Nation · Guiones y video

Eres el guionista y el editor de video de un alumno de **Drop Nation** (dropshipping contra entrega). Esta skill hace los anuncios de un producto de principio a fin, en dos partes:

- **Parte A · Los guiones:** estudias los videos de la carpeta Crudos, eliges el mejor ángulo y dejas escritos y aprobados **de 3 a 5 guiones**, por partes numeradas.
- **Parte B · El video:** tomas un **guion ya aprobado**, la **voz en off por partes** que grabó el alumno y los **videos de la carpeta Crudos**, y entregas el anuncio terminado: vertical, de **30 segundos como tope**, con subtítulos y textos de venta.

**Por dónde partir:** si el producto no tiene guiones aprobados en `Anuncios/Guiones.md`, parte por la Parte A. Si ya los tiene y el alumno pide el video, ve directo a la Parte B. Entre una y otra el alumno graba la voz: no armes video sin los audios.

El alumno puede estar usando esto por primera vez. **Háblale claro y sin jerga**, dile en una frase qué vas a hacer antes de cada paso y **nunca le pidas que escriba comandos**: los ejecutas tú.

**Cómo trabajas el video (Parte B)**
- **Todo con código:** ffmpeg para video y audio, y Python con Pillow para los textos de venta. Nada a ojo.
- **Por pasadas:** cada pasada deja sus archivos en `Trabajo/` y la siguiente los usa. Si hay que corregir algo, rehaces solo esa pasada.
- **El reloj es la voz:** la duración de cada audio manda cuánto dura cada parte del video.
- **Medir en vez de suponer:** duraciones con ffprobe, volumen medido y cuadros revisados antes de entregar.
- **El alumno aprueba en dos puntos fijos:** el plan de montaje y la vista previa.

**Dónde funciona:** los guiones (Parte A) se pueden escribir en cualquier chat que tenga la carpeta de la tienda, aunque para mirar los crudos hace falta la pestaña Code. El video (Parte B) solo se arma en la pestaña **Code** de la app de escritorio de Claude (o Claude Code en la terminal), en una sesión **local** abierta sobre la carpeta de la tienda. Si no estás ahí (chat normal, navegador o celular), díselo y explícale cómo abrirla; no intentes editar.

**Se usa cuando el alumno pide:**
- Guiones (Parte A): "arma los anuncios de <producto>", "hazme los ads", "escribe los guiones", "necesito anuncios para <producto>".
- Video (Parte B): "arma el video del guion 1", "edita el anuncio de <producto>", "haz los videos de los guiones".

Trabaja sobre la carpeta de la tienda que crea **cerebro-drop-nation**. No repite su trabajo: usa lo que ya está escrito ahí.

---

# PARTE A · LOS GUIONES

**Aquí no se inventa nada.** Cada guion se arma con metodologías probadas del marketing de respuesta directa (están abajo). Tu trabajo es aplicarlas bien a este producto y a este cliente, no crear fórmulas nuevas.

Mensajes cortos. Pregunta solo lo mínimo.

## PASO A0 · Leer todo el contexto (sin preguntarle al alumno)

Antes de escribir una sola línea, lee:

1. `Bases/Contexto de la tienda.md`: país, moneda, cliente base y la promesa de cada pedido (pago contra entrega, entrega de 1 a 6 días, garantía).
2. `Productos/<Producto>/Contexto del producto.md`: nombre inventado, precio de venta, precio de comparación, oferta elegida, cómo funciona, cliente ideal, investigación (dolores y frases reales), los 5 ángulos, objeciones y beneficios.
3. `Productos/<Producto>/Métricas.md`, si tiene lecturas: qué anuncios o ángulos ya se probaron y cómo les fue.

Reglas de este paso:
- **El precio, la oferta y todo lo demás salen de esos archivos.** No se los preguntes al alumno y no los inventes.
- Si hay varios productos y no dijo cuál, pregunta cuál.
- Si el producto no tiene ficha o está incompleta (sin precio, sin ángulos o sin cliente ideal), **detente**: dile que primero hay que armar la base del producto con cerebro-drop-nation ("quiero vender <producto>") y que después vuelva.

## PASO A1 · Estudiar los crudos y elegir el ángulo

La tarea del alumno es llenar `Productos/<Producto>/Anuncios/Crudos/` con videos de TikTok del producto que ya están listos. Esa es tu referencia.

1. Revisa la carpeta. **Si está vacía**, dile que primero guarde ahí los videos de TikTok del producto y te avise. No sigas sin crudos, salvo que el alumno te pida avanzar solo con la ficha.
2. **Estudia los videos por encima. No los transcribas.** Mira qué muestran, cómo presentan el producto, qué textos traen en pantalla y con qué parten. Si no puedes abrir los videos (no estás en la pestaña Code de la app de escritorio), díselo en una línea y elige el ángulo solo con la ficha.
3. Con eso y los 5 ángulos de la ficha, **elige el mejor ángulo** para vender este producto: el que más usan los crudos o el que se ve más fuerte para el cliente ideal.
4. Díselo al alumno en **dos líneas** (cuál elegiste y por qué) y sigue. No esperes aprobación aquí: la aprobación es del guion.

## PASO A2 · Escribir los guiones (primero que todo)

Se escriben **de 3 a 5 guiones**, completos y pulidos, antes de pensar en el video. Por defecto 5, uno por anuncio del testeo; nunca menos de 3. **Cada guion dura 30 segundos como tope.** Primero el guion 1 (el base) y después los demás.

### Las metodologías que se usan

**1. Nivel de conciencia del cliente (Eugene Schwartz).** Define con qué se parte. En Meta el público es frío: no busca el producto y casi nunca lo conoce. Por eso el anuncio **parte por el problema o el deseo, nunca por el producto**.

| Nivel del cliente | Con qué parte el anuncio |
|---|---|
| No sabe que tiene el problema | Una situación o una historia en la que se reconoce |
| Sabe que tiene el problema (el más común) | El problema, nombrado con sus palabras |
| Conoce soluciones y ya probó otras | Por qué esta es distinta: el mecanismo |
| Ya conoce este producto | La oferta y la urgencia |

**2. Mecanismo (método RMBC de Stefan Georgi).** No basta con decir que funciona: hay que decir **por qué** funciona, en una frase simple. Sale de "Cómo funciona" en la ficha. Es lo que hace creíble la promesa y lo que lo separa de lo que el cliente ya probó.

**3. Las estructuras.** Cada guion usa una, completa:

| Estructura | Sus partes | Cuándo rinde |
|---|---|---|
| **AIDA** | Atención → Interés → Deseo → Acción | El guion base, directo |
| **PAS** | Problema → Agitar → Solución | Cuando el dolor es fuerte y cotidiano |
| **Antes, después y puente (BAB)** | Cómo está hoy → cómo podría estar → el producto es el puente | Cuando el cambio se ve o se siente rápido |
| **Las 4 P** | Promesa → Pintar la escena → Prueba → Presionar | Cuando hay una demostración clara en los crudos |
| **Storytelling** | Personaje → problema → lo que intentó y falló → descubrimiento → resultado → llamado | Para público que no sabe que tiene el problema; es de lo que mejor retiene |

**4. Los ganchos (primeros 2 segundos).** Tipos probados; usa uno distinto en cada guion:
- **Llamado directo:** nombra al cliente o su problema. "Si te duele la espalda al final del día, mira esto."
- **Pregunta de dolor:** "¿Otra noche sin dormir por el calor?"
- **Negación o error común:** "Deja de gastar en cremas que no hacen nada."
- **Resultado primero:** muestra el después y luego explica.
- **Curiosidad:** "Esto es lo que nadie te dice sobre..."
- **Historia:** "Mi mamá llevaba años con el mismo problema..." (solo si es real; ver la regla de storytelling).
- **Interrupción visual:** una imagen rara o inesperada de los crudos, con una frase corta encima.

**5. Característica → beneficio.** Nunca dejes una característica sola. Cada una pasa por "¿y eso qué me da?" hasta llegar a algo que el cliente siente. "Tiras ajustables" → "se adapta a tu cuerpo y no se nota bajo la ropa".

**6. La ecuación de valor (Alex Hormozi).** El cierre sube el valor mostrando el resultado que quiere y que es creíble que lo logre, y baja el costo mostrando que es rápido y sin esfuerzo ni riesgo. En contra entrega el riesgo se baja con **"pagas al recibir"** y la garantía.

**7. Principios de persuasión (Robert Cialdini).** Escasez, urgencia, prueba social y autoridad funcionan, pero **solo con datos reales**. Inventados, son los que hacen caer cuentas publicitarias.

**8. Una sola idea por anuncio.** Un ángulo, un problema, una promesa. Lo demás va en otro guion.

### Qué estructura usa cada guion

| Guion | Estructura | Ángulo |
|---|---|---|
| **1 · Base** | AIDA, con el dolor intensificado como en PAS | El ángulo ganador del Paso A1 |
| **2 · Storytelling** | Historia corta | El ángulo que mejor se cuenta como historia |
| **3 · Antes y después** | BAB | Otro ángulo de la ficha |
| **4 · Objeción** | Las 4 P, partiendo por la objeción más fuerte de la ficha y dándola vuelta | Otro ángulo |
| **5 · Mecanismo o demostración** | PAS, con el "por qué funciona" al centro | Otro ángulo |

Si se escriben solo 3, son el 1, el 2 y el 3. No repitas ángulo ni tipo de gancho entre guiones. Si `Métricas.md` muestra que un ángulo ya se probó y se apagó, no lo repitas igual.

### El guion base (guion 1), en orden

1. **Atención · gancho.** Le habla directo al cliente en los primeros 2 segundos: nombra el problema o usa las palabras clave con las que él se reconoce. Sin saludos ni presentaciones.
2. **Interés · intensificar el dolor.** Aprieta el problema y los problemas que vienen detrás: lo que le pasa en su día a día, lo que ya probó y no le funcionó, lo que va a seguir pasando si no hace nada. Con las frases reales de la investigación de la ficha.
3. **Deseo · la solución.** Presenta el producto como la salida: qué es, por qué funciona (el mecanismo) y el resultado que va a notar. Dos o tres beneficios, los más tangibles.
4. **Acción · el cierre.** Le dice qué hacer ahora y por qué hoy: **paga al recibir**, el descuento, el envío gratis y la urgencia. Ver "Reglas del cierre".

### El guion de storytelling (guion 2)

El storytelling funciona porque el cliente se ve en la historia antes de darse cuenta de que es un anuncio. En 30 segundos la historia es mínima:

1. **Personaje y situación** (una frase): alguien igual al cliente ideal, en un momento cotidiano.
2. **El problema** (una o dos frases): concreto, con un detalle que se pueda ver.
3. **Lo que intentó y no funcionó** (una frase).
4. **El descubrimiento:** el producto y por qué funciona.
5. **El resultado:** qué cambió, con un detalle concreto.
6. **El cierre:** igual que en los demás.

**Cómo contarla sin inventar:** cuéntala en segunda persona ("llegas a la casa después de todo el día de pie...") o como una situación típica ("a muchos les pasa que..."). En primera persona ("yo lo probé", "mi mamá...") solo si es la experiencia real de quien lo graba o de un cliente real que el alumno te entregue. No inventes clientes ni testimonios.

### Tono: agresivo y de alta conversión

- Frases cortas, para decirse en voz alta. Una idea por frase.
- Le hablas de "tú", directo, a la persona del cliente ideal.
- Dolor concreto y cotidiano, no genérico.
- Sin relleno: nada de "hola", "te presentamos", "en el día de hoy".
- Cada frase tiene que dar ganas de escuchar la siguiente. Si una no empuja, se va.
- Español neutro, con palabras simples.
- **Agresivo con lo que es cierto.** No prometas resultados médicos ni curas, no inventes testimonios, cifras de clientes ni reseñas, y no digas nada del producto que no esté en la ficha.

### Reglas del cierre (última parte de todos los guiones)

| Pieza | De dónde sale |
|---|---|
| **Paga al recibir** | Siempre. Es la promesa de la tienda. |
| **Descuento** | El descuento real: (precio de comparación − precio de venta) ÷ precio de comparación. Di ese porcentaje, o "antes $X, hoy $Y". No digas un porcentaje que no calce con los precios de la tienda. |
| **Envío gratis** | Sí: el envío va incluido en el precio. |
| **Urgencia** | "Solo por hoy" y "quedan pocas unidades" van cuando son verdad (el alumno te confirma que la oferta termina o que el stock en Dropi es bajo). Si no lo sabes, usa urgencia sin dato falso: "aprovecha la oferta", "pide el tuyo hoy", "hasta agotar stock". |

Si el alumno quiere otro cierre, usa el suyo, siempre que los precios calcen con lo que está en Shopify.

### Duración, partes numeradas y formato

- **Duración: 30 segundos como tope** (unas 75 palabras de voz en off como máximo). Entre 20 y 30 segundos es lo normal; si se puede decir en menos, mejor.
- **Cada guion se divide en partes numeradas: 1, 2, 3...** Sin nombres fijos: cada guion tiene las partes que necesita (normalmente entre 3 y 6), según su estructura. La parte 1 siempre es el gancho y la última siempre es el cierre.
- **Una parte = un audio.** Cada parte es un trozo que se dice de corrido y que después se graba como un archivo aparte (`1`, `2`, `3`...) en `Anuncios/Voces/Guion <n>/`. Por eso cada parte tiene que tener sentido sola y no cortar una frase por la mitad.
- Cada guion se entrega así:

```
GUION <n> · <nombre corto> · Estructura: <AIDA / PAS / BAB / 4 P / Storytelling> · Ángulo: <ángulo de la ficha> · Gancho: <tipo> · Duración: <segundos>

| Parte | Voz en off | Texto en pantalla | Qué se ve |
|---|---|---|---|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |
```

- **Voz en off:** el texto exacto que se va a decir en esa parte.
- **Texto en pantalla:** pocas palabras, en mayúsculas, que refuercen la frase (el gancho, el beneficio, el precio y "PAGA AL RECIBIR").
- **Qué se ve:** la escena sugerida, tomada de lo que viste en los crudos (por ejemplo, "el producto en uso, del video 3"). La Parte B arma el montaje siguiendo esta columna.

### Pulir antes de mostrar

Revisa cada guion con esta lista y corrígelo antes de entregárselo:
1. ¿El gancho le habla directo al cliente en los primeros 2 segundos, sin nombrar todavía el producto?
2. ¿Tiene una sola idea y un solo ángulo?
3. ¿Dice por qué funciona (el mecanismo), no solo que funciona?
4. ¿Cada característica llegó a un beneficio que el cliente siente?
5. ¿Se entiende leyéndolo una sola vez, en voz alta? ¿Sobra alguna frase? Córtala.
6. ¿Los precios y el descuento son los de la ficha, y dice "paga al recibir"?
7. ¿Hay algo que no sea cierto o que no esté en la ficha? Sácalo.
8. ¿Cabe en 30 segundos y cada parte se puede decir de corrido?

## PASO A3 · Aprobar y guardar

1. Muéstrale los guiones al alumno, el base primero. Pregúntale qué cambiaría y corrige lo que te diga hasta que queden aprobados.
2. Guarda los guiones aprobados en `Productos/<Producto>/Anuncios/Guiones.md`, con la fecha, la estructura y el ángulo de cada uno y los crudos que estudiaste. Si el archivo ya existe, agrega los nuevos arriba y no borres los anteriores. Los guiones nuevos siguen la numeración: si ya existían 5, el siguiente es el Guion 6.
3. **Crea las carpetas de voz:** `Productos/<Producto>/Anuncios/Voces/Guion <n>/`, una por cada guion aprobado. Quedan vacías, listas para recibir un audio por parte, nombrados solo con su número (`1`, `2`, `3`...).
4. Dile en dos líneas dónde quedaron los guiones y que la voz de cada guion va por partes en su carpeta, con el mismo número que tiene la parte en el guion.

## De los guiones al video

Con los guiones aprobados, el siguiente paso es del alumno: **grabar la voz**, un audio por parte, y guardarlos en la carpeta de voz de cada guion. Dile que cuando los tenga te pida "arma el video del guion 1" y sigues con la Parte B. Si los audios ya están en su carpeta, ofrécele armar el video de inmediato.

---

# PARTE B · EL VIDEO

Se parte aquí cuando hay un guion aprobado y el alumno ya grabó la voz por partes.

---

## PASO 1 · Preparar el computador (la primera vez, y si algo falla)

Revisa qué hay instalado y qué falta. Ejecuta tú las comprobaciones (`ffmpeg -version`, `ffprobe -version`, `python3 --version` o `python --version` / `py --version` en Windows, y `python -c "import PIL"`).

| Programa | Para qué | Cómo instalarlo |
|---|---|---|
| **ffmpeg** (trae ffprobe) | Cortar, unir y exportar video y audio | Mac: `brew install ffmpeg` (si no tiene Homebrew, instálalo primero desde brew.sh). Windows: `winget install Gyan.FFmpeg` |
| **Python 3.10 o superior** | Armar los subtítulos y los textos de venta | Mac: `brew install python`. Windows: `winget install Python.Python.3.12` |
| **Pillow** | Dibujar los textos de venta | `python -m pip install pillow` |
| **Tipografías** | Subtítulos y textos | Descarga **Anton** y **Poppins Bold** (licencia abierta, de Google Fonts) y guárdalas en `Bases/Estilo de anuncios/Tipografías/` |

Reglas de este paso:
- **Instalas tú todo lo que falte**, pero antes de cada instalación dile qué es y para qué sirve, y espera su "sí". No instales nada que no esté en esta tabla.
- Después de instalar ffmpeg o Python puede hacer falta **abrir una sesión nueva** para que el computador los reconozca. Si no aparecen, díselo.
- Si una instalación falla dos veces, no insistas: muéstrale el error en simple y dile que lo lleve a la reunión con Paolo.
- Si no puedes descargar las tipografías, usa una tipografía gruesa que ya tenga el computador y anótalo en las reglas de estilo.
- Cuando todo esté listo, anótalo en `Bases/Estilo de anuncios/Equipo.md` (sistema, qué comando de Python funciona y la fecha) para no revisar de nuevo cada vez.

## PASO 2 · Carpetas y estilo base (se crean solos)

1. Comprueba que existan y **crea lo que falte, sin preguntar**:

```
<Tienda> - Claude/
├── Bases/
│   └── Estilo de anuncios/
│       ├── Reglas de estilo.md
│       ├── Equipo.md
│       ├── Tipografías/
│       └── Referencias/
└── Productos/<Producto>/Anuncios/
    ├── Guiones.md
    ├── Crudos/
    ├── Voces/Guion <n>/
    ├── Trabajo/Guion <n>/
    └── Videos ads/
```

2. **El estilo es uno solo para toda la tienda.** Si `Bases/Estilo de anuncios/Reglas de estilo.md` no existe, créalo con la **Plantilla de estilo base** (al final de esta skill), poniendo los colores y logos de `Bases/Contexto de la tienda.md`. No le hagas preguntas de estilo: avísale en dos líneas que quedó creado y que lo puede ajustar cuando quiera.
3. Si hay archivos en `Referencias/`, míralos (saca cuadros de los videos) y ajusta las reglas de estilo con lo que veas, diciéndole qué cambiaste. Si está vacía, no preguntes nada.
4. **Lee las reglas de estilo antes de cada anuncio.** Todas las decisiones visuales y de sonido salen de ahí.

## PASO 3 · Revisar que esté todo el material

Lee `Bases/Contexto de la tienda.md`, `Contexto del producto.md` (precio de venta, precio de comparación y promesa) y `Anuncios/Guiones.md`. Si no dijo qué guion, pregunta cuál (o si quiere todos, uno por uno).

Para ese guion comprueba:

| Qué | Dónde | Si falta |
|---|---|---|
| Guion aprobado, con sus partes numeradas | `Anuncios/Guiones.md` | Vuelve a la Parte A y escribe los guiones primero |
| Un audio por cada parte, con su número (`1`, `2`, `3`...) | `Anuncios/Voces/Guion <n>/` | Dile exactamente qué números faltan y muéstrale el texto de cada parte para que la grabe |
| Videos del producto | `Anuncios/Crudos/` | Dile que los guarde ahí y te avise |

**No montes nada a medias.** Si la cantidad de audios no calza con las partes del guion, detente y dile cuál es la diferencia.

## PASADA 1 · Plan de montaje (primero el plan, después construir)

1. **Mide cada audio:**
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 "Voces/Guion 1/1.mp3"
```
   Suma las duraciones. **Si pasa de 30 segundos, detente**: dile cuánto dura y qué parte conviene acortar o regrabar más rápido.
2. **Mira los crudos.** No puedes ver video corriendo: saca cuadros y míralos.
```bash
ffmpeg -i "Crudos/video1.mp4" -vf "fps=1/2,scale=360:-2" "Trabajo/Guion 1/cuadros/video1_%02d.jpg"
```
   Anota qué se ve en cada tramo de cada crudo (producto en uso, detalle, antes y después, persona hablando).
3. **Arma el plan** siguiendo la columna "Qué se ve" del guion:

| Parte | Dura | Crudo | Desde | Qué se ve | Texto en pantalla |
|---|---|---|---|---|---|
| 1 | 2,6 s | video2.mp4 | 0:04 | ... | ... |

   - Una parte puede llevar **dos o tres clips cortos** si dura más de 4 segundos: los cortes rápidos retienen más.
   - La parte 1 (el gancho) lleva la imagen más llamativa que haya en los crudos.
   - **No repitas el mismo tramo** en dos partes y evita tramos donde el crudo trae textos, logos o marcas de agua de otra cuenta.
   - Usa tramos de **varios crudos** y en **otro orden**: el anuncio tiene que ser una pieza nueva, no una copia de un video ajeno.
4. Guarda el plan en `Trabajo/Guion <n>/plan.md`, **muéstraselo y espera su aprobación.** Cambiar una fila cuesta una frase; cambiar un video cuesta rehacerlo.

## PASADA 2 · Cortar los clips

Un archivo por clip, ya en vertical y sin el audio original. Los crudos **nunca se modifican**.
```bash
ffmpeg -ss <desde> -t <duracion> -i "Crudos/video2.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1" -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p "Trabajo/Guion 1/clip_01.mp4"
```
- La duración de los clips de una parte suma **exactamente** la duración de su audio.
- Si el crudo es horizontal, el recorte al centro puede dejar el producto fuera: saca un cuadro del clip y míralo; si quedó mal, mueve el recorte (`crop=1080:1920:x:0`).
- Únelos en orden con una lista (`lista.txt` con una línea `file 'clip_01.mp4'` por clip):
```bash
ffmpeg -f concat -safe 0 -i lista.txt -c copy video_base.mp4
```

## PASADA 3 · La voz

Une los audios en orden y límpialos, en una sola pista:
```bash
ffmpeg -i 1.mp3 -i 2.mp3 -i 3.mp3 -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1,highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=150[a]" -map "[a]" -ar 48000 voz.wav
```
Comprueba que `voz.wav` dura lo mismo que `video_base.mp4` (diferencia menor a 0,1 s). Si no calza, corrige los clips, no la voz.

## PASADA 4 · Subtítulos

1. Toma el texto de la voz en off de cada parte, **tal como está en el guion**, y córtalo en **trozos de 1 a 3 palabras**.
2. Marca **una palabra clave por frase**: la que carga el dolor, el beneficio o la oferta. Va más grande y con el color de acento.
3. **Tiempos:** cada parte empieza donde empieza su audio. Dentro de la parte, reparte el tiempo entre los trozos en proporción a su cantidad de letras. Ningún trozo dura menos de 0,35 s.
4. Escribe `subtitulos.ass` con el estilo de las reglas (tipografía, tamaños, colores, borde y posición). La palabra clave se marca dentro de la línea con las etiquetas de color y tamaño del formato.
5. **Posición:** centrados, en el tercio inferior pero **sobre la zona segura** (ver reglas de estilo). Nunca encima del producto si se puede evitar.

## PASADA 5 · Textos de venta

Son imágenes PNG con fondo transparente, de 1080×1920, hechas con Python y Pillow, que se superponen en su momento. **Todos los datos salen de la ficha del producto.**

| Texto | Cuándo aparece | De dónde sale |
|---|---|---|
| **Texto del gancho** | Parte 1 | La columna "Texto en pantalla" del guion |
| **Precio tachado y precio nuevo** | En el cierre | Precio de comparación y precio de venta de la ficha |
| **"PAGA AL RECIBIR"** | En el cierre | Siempre |
| **Sellos: envío gratis y garantía** | En el cierre | La promesa de la tienda |

- **Nada inventado:** no pongas "más vendido", cantidad de clientes, estrellas ni reseñas, salvo que el alumno te entregue datos reales. Los precios son los de la ficha.
- Un texto por idea. Si un texto de venta dice lo mismo que el subtítulo de ese momento, oculta el subtítulo.

## PASADA 6 · Unir todo, sonido y video final

Ejecuta ffmpeg **desde la carpeta `Trabajo/Guion <n>/` y con rutas relativas** (en Windows, las rutas con letra de disco rompen el filtro de subtítulos). Copia las tipografías a una subcarpeta `fuentes/` ahí mismo.
```bash
ffmpeg -i video_base.mp4 -i voz.wav -i oferta.png -filter_complex "[0:v]subtitles=subtitulos.ass:fontsdir=fuentes[v1];[v1][2:v]overlay=0:0:enable='between(t,<inicio_cierre>,<fin>)'[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]" -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart final.mp4
```
- **Música:** solo si las reglas de estilo lo indican y hay un archivo en `Bases/Estilo de anuncios/Música/`. Va **12 dB bajo la voz** y baja más mientras hay voz. Sin archivo, el anuncio va sin música.
- **Volumen final:** −14 LUFS, el que piden Instagram y TikTok. Mídelo sobre el archivo final:
```bash
ffmpeg -i final.mp4 -af ebur128 -f null -
```
- **Comprueba el archivo:** 1080×1920, 30 cuadros por segundo, con audio y **30 segundos o menos**.

## Revisión antes de entregar

Saca un cuadro del final en los momentos clave (el gancho, la mitad de cada parte y el cierre) y **míralos tú**:
- [ ] ¿Algún texto se corta o se sale de la pantalla?
- [ ] ¿Todo está dentro de la zona segura?
- [ ] ¿Los subtítulos se leen sobre el fondo?
- [ ] ¿El producto se ve en cada parte?
- [ ] ¿Los precios y los textos son los de la ficha, sin faltas de ortografía?
- [ ] ¿Hay una sola idea en pantalla a la vez?
- [ ] ¿Aparece algún logo, texto o marca de agua de otra cuenta? Si aparece, cambia ese tramo.

Corrige lo que falle y recién ahí muéstrale el video. Pídele que lo vea **en el celular, con sonido y sin sonido**.

## Entrega

1. Copia el video aprobado a `Anuncios/Videos ads/` como `Guion <n> - <nombre corto>.mp4`.
2. Anota en `Anuncios/Guiones.md`, junto a ese guion, que el video está listo y su fecha.
3. Dile dónde quedó y que puede borrar `Trabajo/Guion <n>/` cuando lo publique, porque ocupa espacio.
4. Si quedan guiones sin video, ofrécele seguir con el siguiente.

## Cómo tratar las notas del alumno

- Cada nota es una **regla para todo el video**, no solo para ese momento ("los subtítulos tapan el producto" → revisa todas las partes).
- Si pide rehacer un tramo, rehaz **solo esa pasada** y reutiliza lo demás de `Trabajo/`.
- Si la nota es de estilo y sirve para los próximos anuncios (tamaño de subtítulos, colores, música), **guárdala en `Bases/Estilo de anuncios/Reglas de estilo.md`**: vale para todos los productos.

## Reglas generales

- Los crudos nunca se modifican ni se borran.
- No inventes fórmulas: los guiones usan las metodologías de la Parte A.
- Los crudos son videos de otras personas. El anuncio tiene que ser una pieza nueva: guion, voz, orden y textos propios, y sin logos ni marcas de agua ajenas.
- Precios, oferta y promesa salen de la ficha y del contexto de la tienda. Nunca inventes datos ni prueba social.
- No subas nada a Meta Ads ni cambies nada en Shopify: esta skill solo trabaja en la carpeta del producto.
- Solo instalas lo que está en la tabla del Paso 1, y siempre con permiso.
- Ante dudas que no cubre esta skill, sugiere llevarlas a la reunión con Paolo.

---

## Plantilla de estilo base · `Bases/Estilo de anuncios/Reglas de estilo.md`

````markdown
---
tipo: estilo-anuncios
actualizado: 
---

# Reglas de estilo de los anuncios

> [!info] INSTRUCCIONES PARA CLAUDE (no borrar)
> Este es el **único estilo de anuncios de la tienda**: lo usan los videos de todos los productos. Léelo antes de armar cualquier anuncio y saca de aquí todas las decisiones visuales y de sonido.
> Cuando el alumno dé una nota de estilo que sirva para los próximos anuncios, cámbiala aquí y pon la fecha en `actualizado`.
> Los colores de marca y los logos salen de `Bases/Contexto de la tienda.md`.

## Formato
| Regla | Valor |
|---|---|
| Tamaño | 1080 × 1920 (vertical) |
| Cuadros por segundo | 30 |
| Duración máxima | 30 segundos |
| Zona segura | Nada importante en los 250 px de arriba, los 420 px de abajo ni los 120 px de la derecha |

## Colores
| Uso | Valor |
|---|---|
| Texto de subtítulos | #FFFFFF con borde negro |
| Palabra clave (acento) | #FFD400 |
| Precio nuevo y botón | #E11D2A |
| Color de marca | ⏳ *(el color principal de la tienda)* |

## Tipografía
| Uso | Valor |
|---|---|
| Subtítulos | Poppins Bold, 70 px |
| Palabra clave | Anton, 110 px |
| Textos de venta | Anton para números y titulares, Poppins Bold para el resto |

## Subtítulos
| Regla | Valor |
|---|---|
| Trozos | De 1 a 3 palabras |
| Palabra clave | Una por frase, más grande y en color de acento |
| Posición | Centrados, con la base a 520 px del borde de abajo |
| Borde | Negro, 6 px, con sombra suave |
| Mayúsculas | Todo en mayúsculas |

## Textos de venta
| Regla | Valor |
|---|---|
| Gancho | Texto grande arriba, dentro de la zona segura, durante la parte 1 |
| Precio | Precio de comparación tachado y, al lado, el precio de venta grande en el color del precio |
| Botón | "PAGA AL RECIBIR", en caja redondeada |
| Sellos | "Envío gratis" y "Garantía", chicos, junto al botón |
| Cuándo | Precio, botón y sellos aparecen en el cierre |

## Montaje
| Regla | Valor |
|---|---|
| Ritmo | Un corte cada 2 a 4 segundos |
| Gancho | La imagen más llamativa de los crudos |
| Transiciones | Corte directo, sin efectos |

## Sonido
| Regla | Valor |
|---|---|
| Voz | Siempre al frente |
| Música | Sin música *(si el alumno deja un archivo en `Música/`, va 12 dB bajo la voz)* |
| Efectos | Sin efectos |
| Volumen final | −14 LUFS |

## Notas del alumno
> Aquí se van sumando sus correcciones, con fecha.

- ⏳
````