---
tipo: guia-estilo-motion
estilo: Explicador Ilustrado
id: explicador-ilustrado
version: 1.1.0
actualizado: 2026-11-17
---

# Guía de estilo · Explicador Ilustrado

> [!info] PARA CLAUDE (no borrar)
> Esta guía **manda** en todo video de este estilo. Los números exactos están en `estilo.json`; las recetas animadas, en `plantilla/assets/estilo.js`; un video armado completo, en `plantilla/index.html`. Parte **siempre** copiando `plantilla/` a `Trabajo/<Idea>/` y cambiando escenas, palabras y sonidos. Cada regla dice si es **[medido]** en las referencias o **[mejora]** nuestra sobre el original. Las mejoras van activadas por defecto.

## 1. Qué es este estilo (en una frase)

Explicador curioso con **ilustración semirrealista suave sobre fondos oscuros con acentos neón**: la cámara nunca está quieta, **se mete "por dentro"** del cuerpo o del objeto y salta a **metáforas cotidianas**. Lo narra una voz rápida con **subtítulos karaoke arriba** y **muchos efectos de sonido, sin música**.

## 2. Formato

- 1080×1920 (9:16), 30 fps, 60 a 90 s. **[medido: 66-91 s]**
- Contenido dentro del 90 % de pantalla; textos dentro del 80 %. Deja libre el 12 % de abajo para la interfaz de Instagram y TikTok. **[mejora]**

## 3. Look (cómo se ve)

| Elemento | Regla |
|---|---|
| Fondo | Oscuro **morado** (`#1E1033`) o **azul noche** (`#0B0A22`), con brillo radial al centro y viñeta. Nunca degradado lineal a pantalla completa. **[medido]** |
| Personaje u objeto | Ilustración **semirrealista suave**: degradados de aire, brillo interno, sin contorno negro, volumen con luz de arriba. Piel `#DB9176` y tejido `#E55F6B`. **[medido]** |
| Acento | **Un solo neón protagonista por escena**: rosa `#FF3FA4`, cian `#43D9FF` u oro `#FFC94A`, siempre con resplandor. **[medido]** |
| Grading | Brillo 33/100, contraste 17, saturación 51, levemente frío. **[medido]** |
| Partículas | Bokeh o polvo flotando en casi todas las escenas (20 a 35 puntos). **[medido]** |

**Cómo se dibuja** (por orden de preferencia):
1. **SVG por código** para objetos simples (celular, batería, ampolletas, auto, reloj, íconos): degradados lineales y radiales + `brillo-neon`. La demo está hecha así.
2. **Imagen del producto** que dejó el cerebro en `Imágenes/`, recortada y animada por capas (cámara, glow encima, etiquetas).
3. **Ilustración base generada con Canva** para lo orgánico (piel, ojos, pierna, corte de tejido), con este prompt fijo, y luego animada por código encima:
   > *Ilustración médica semirrealista 2D para video vertical 9:16, estilo explicador de redes sociales, degradados suaves tipo aerógrafo, sin contornos negros, fondo [morado oscuro #1E1033 / azul noche #0B0A22] con brillo radial al centro y viñeta, iluminación cinematográfica suave, [SUJETO], vista [lateral/frontal/corte transversal], sin texto.*

## 4. Ritmo y cámara

- **Cámara siempre viva** [medido: 94 % de planos con movimiento]: deriva lenta de escala 1,00→1,10 con `sine.inOut` (`EI.camara`). Alterna planos que se acercan y planos que se alejan.
- **Empujón** en la palabra fuerte: +6 % en 0,18 s (`EI.empujon`). **Sacudida** de 14 px en golpes y dolor (`EI.sacudida`).
- **Plano de 2 a 4,5 s** [mejora: el original promedia 6,4 s y tiene planos de 10-20 s que bajan la retención]. Si un plano dura más, mete un **evento visual cada 2 s como máximo**: etiqueta, onda, pulso neón, empujón o globo.
- **Gancho:** algo se **transforma antes de 0,8 s** (la pierna se pone gris, la ceja se arranca) y hay un cambio de escena antes de los 4 s [mejora: el original corta recién a los 6,6 s].

## 5. Transiciones

| Transición | Cuándo | Receta |
|---|---|---|
| **Entrar con zoom** (10 %) | De afuera a "por dentro" (piel→folículo, celular→batería). Es la firma del estilo. | `EI.entrarZoom` 0,45 s `power3.in` + entra desde 0,7 |
| **Fundido** (31 %) | Misma idea, otro momento | `EI.fundido` 0,35 s |
| **Corte seco** (37 %) | Cambio de idea, **siempre con golpe** | `EI.corte` + `tick`/`impacto` |
| **Barrido con desenfoque** (15 %) | Salto a una metáfora | `EI.barrido` 0,22 s, blur 22 px |
| **Destello** | Paso del tiempo (día/noche) o revelación del dato | `EI.destello` |

## 6. Subtítulos (karaoke acumulativo) · `EI.karaoke`

- **Arriba**, centro del bloque al ~19 % de la altura (`top: 300px`), centrados, máximo 2 líneas y 6 palabras. **[medido]**
- **Poppins 600, 70 px** [mejora: el original va a ~52 px y cuesta leerlo en el celular], sombra suave.
- La frase **se va armando**: la palabra que suena entra en **blanco** (0,12 s, sube 10 px) y las ya dichas bajan a **gris `#8E8C9A`**. **[medido]**
- **Una palabra clave por frase** con **caja azul `#2F7BFF` y manijas** (como una selección de diseño). Marca con `clave: true` la palabra que lleva el sentido (QUEMA, iones, calor). **[medido + mejora: el original la usa al azar; nosotros siempre en la palabra fuerte]**
- Mayormente minúsculas; MAYÚSCULAS solo en la palabra clave del gancho y en la palabra para comentar.
- Los tiempos salen de la voz medida (Piper + transcripción), nunca a ojo.

## 7. Recursos del estilo (y su receta)

| Recurso | Para qué | Receta |
|---|---|---|
| Corte por dentro | Mostrar el mecanismo | Capas SVG + `EI.entrarZoom` |
| Línea neón + pulsos | Nervios, señales, cables, corriente | `EI.neonDibujar` → `EI.neonPulso` |
| Ondas concéntricas | Wifi, sonido, calor, dolor | `EI.ondas` (círculos SVG con `cx`/`cy`) |
| Metáfora cotidiana | Que se entienda en 1 s | Escena aparte con `EI.barrido` |
| Etiqueta píldora | Nombrar una parte ("solo piel") | `.etiqueta` + `EI.pop` |
| Globo ícono | "?", "Zz", "!" | `.globo` + `EI.pop` |
| Lupa | Revelar un detalle | `.lupa` + `EI.lupa` |
| Contador | Grados, %, km/h | `EI.contador` |
| Partículas | Atmósfera | `EI.particulas` (con semilla) |
| Paso del tiempo | Días, meses | `EI.destello` en serie + reloj/calendario |
| Burbuja de comentario | Cierre | `.burbuja` + `EI.pop` + `burbuja.wav` |

## 8. Sonido

- **Sin música** [medido: piso −78 dB y 22 % de silencio]: la pone el editor. Voz al frente, mezcla a **−14 LUFS**.
- **45 a 60 efectos por minuto** [medido: 54]. Mapa fijo: transición→`whoosh`, etiqueta o globo→`pop`, palabra clave→`tick`, gancho→`impacto`, destello→`brillo`, pulso neón→`pulso`, cierre→`burbuja`.
- **Cada corte lleva golpe** [mejora: el original solo en el 25 %; nosotros en ≥80 %].
- Los sonidos se crean con `herramientas/generar_sfx.py` (no se descarga nada).

## 9. Voz y guion

- Voz rápida: **3 a 3,6 palabras por segundo**; la primera palabra suena a los 0,15 s. Sin presentaciones.
- Estructura medida en las 4 referencias:
  1. **Gancho** que te nombra a ti: pregunta ("¿Por qué se te duerme la pierna…?") o condición ("Si de adolescente te arrancaste las cejas…").
  2. **Revelación:** "Tu pierna no está dormida: está desconectada."
  3. **Por dentro:** el mecanismo, entrando con zoom.
  4. **Metáfora cotidiana** (auto en la carretera, ampolletas).
  5. **Vuelta al mecanismo + consecuencia.**
  6. **Dato o consejo.**
  7. **Cierre** con burbuja.
- **[mejora para productos]** En el paso 5 o 6 el **producto aparece como la solución**, dentro de la misma lógica por dentro. El cierre lo elige el alumno: oferta + paga al recibir, o "comenta <PALABRA>".
- **[mejora]** **Bucle:** el último cuadro se parece al primero, para que se vuelva a ver.

## 10. Storyboard con la gramática del estilo

La gramática medida está en `estilo.json → gramatica` [medido v2]: planos de mediana ~4 s, **algo nuevo cada ~1,7 s** (cortes + eventos dentro del plano), cámara 32 % acercamiento · 26 % alejamiento · 11 % deriva · 8 % paneo · 8 % giro, y el mismo movimiento repetido seguido solo en el 16 % de los casos.

- **Siempre** parte de `storyboard.py esqueleto` (3 variantes) y completa `que_se_ve` y `texto_voz`. Elige el de mejor puntaje con `storyboard.py puntuar` (meta: ≥ 90) y corrige lo que liste.
- **Nunca 3 planos seguidos con el mismo movimiento**; ningún plano quieto en la variante dinámica.
- El storyboard aprobado se pasa por `storyboard.py afinar` para que el estilo aprenda.
- Ejemplos y puntaje en `Storyboards/`: los generados sacan 87-94 y las referencias 60-70, porque las referencias fallan en retención (corte tardío y pocos golpes en los cortes).

## 11. Checklist antes de entregar (medir, no suponer)

- [ ] `npx hyperframes check` sin errores.
- [ ] `python3 Herramientas/extraer_estilo.py final.mp4 Trabajo/<Idea>/control --rapido` → la tabla de retención pasa entera.
- [ ] Cuadros clave revisados con los ojos: gancho (0-3 s), cada transición y el cierre.
- [ ] Subtítulos legibles en el celular y nada tapado por la interfaz de abajo.
- [ ] Comparado lado a lado con una referencia (`herramientas/comparar.py`).

## 12. Historial del estilo

- 2026-11-17 · v1.0.0 · Creado desde 4 referencias con el proceso de extracción v2 (medición + lectura cuadro a cuadro + clon + mejora). Demo: `ejemplo/demo.mp4`.
- 2026-11-17 · v1.1.0 · Re-medido con el extractor v2: gramática del estilo, storyboard real de cada referencia, eventos dentro de los planos y subtítulos karaoke. Se suman los storyboards de ejemplo y el puntaje.
