# Informe de extracción (v2.0.0)

> Medidas automáticas en 117 s. La lectura visual (Fase B) y la prueba de clon (Fase D) las completa Claude.

**Referencias:** 4 · **duración media:** 77.94 s · **fps:** [30.0] · **tamaño:** ['720x1280']

## Tabla de retención (Fase E)

| Regla | Valor medio | ¿El original cumple? | Referencias que pasan |
|---|---|---|---|
| Algo cambia en pantalla antes de 0,8 s | 0.32 | ✅ | 3/4 |
| Primer cambio de escena antes de 4 s | 6.66 | ❌ → [mejora] | 0/4 |
| Plano mediano entre 2 y 4,5 s | 3.83 | ✅ | 2/4 |
| Algo nuevo pasa cada ≤ 2 s (cortes + eventos) | 1.69 | ✅ | 4/4 |
| Letra de subtítulo ≥ 46 px de alto a 1920 (≈ 64 px de cuerpo) | 53.0 | ✅ | 4/4 |
| Poca acción en el 12 % de abajo (interfaz de la app) ≤ 12 % | 6.75 | ✅ | 4/4 |
| Golpe de sonido en ≥ 80 % de los cortes | 22.07 | ❌ → [mejora] | 0/4 |
| Entre 40 y 70 efectos por minuto | 54.62 | ✅ | 4/4 |

## Ritmo

- Plano medio **5.03 s** (mediana 3.83 s) · **11.2 cortes/min** · **24.77 eventos/min** dentro de los planos.
- Algo nuevo pasa cada **1.69 s** · primer cambio visual a los **0.32 s** · primer corte a los **6.66 s**.
- Duración de plano (p10 · p50 · p90): 0.37 · 4.08 · 10.7 s.

## Transiciones (% de planos)

- corte seco: 37.1%
- fundido: 30.6%
- barrido: 14.5%
- entrar con zoom: 9.7%
- inicio: 6.5%
- paso por negro: 1.6%

## Cámara (se mueve en el 86.0% de los planos)

- acercamiento: 32.3%
- alejamiento: 25.8%
- quieto: 14.5%
- deriva leve: 11.3%
- paneo horizontal: 8.1%
- giro: 8.1%
- Zoom por plano (p50 · p90): 26.3 % · 74.34 % · paneo por plano: 312.6 px · 863.52 px · sacudida en el 53.2% de los planos.
- Mismo movimiento dos planos seguidos: 16% · easing: none 42%, power2.out 27%, — 13%, power2.in 11%, sine.inOut 6%

## Color

- Brillo 33.0 · contraste 17.0 · saturación 50.7 · temperatura -3.1 · negros 20.7%
- Acentos vivos: `#C71768` `#358DCC` `#DE5261` `#D58B45` `#406ABD` `#46ADEA`
- De adolescente te CORTABAS las cejas..#c: `#DB9176` `#E55F6B` `#A07063` `#82394F` `#ECBA9C` `#B34960`  · fondos: `#4D2331`
- Las legañas no te salen solo de noche, l: `#362E38` `#52434C` `#71544C` `#906A5A` `#191722` `#C3958D`  · fondos: `#362E38` `#52434C` `#191722`
- ¿Alguna vez te preguntaste cómo llega la: `#070A1E` `#171836` `#222B54` `#364473` `#713F33` `#606D8D`  · fondos: `#171836` `#222B54`
- ¿Por qué se te duerme la pierna y luego : `#170F2A` `#763672` `#30193C` `#542B5F` `#65564D` `#AC8B89`  · fondos: `#170F2A` `#30193C`

## Composición

- Arriba 22.0% · centro 51.5% · abajo 26.2% · zona de la interfaz (12 % de abajo) 6.8%

## Subtítulos

- Centro de la franja al **19.0%** de la altura · alto de letra ≈ **53.0 px** a 1920 (≈ 72 px de cuerpo).
- Karaoke (activa + dichas en otro tono) en el **76.0%** del tiempo con texto · **2.65 cambios/s** · mayúsculas 2.0% · hay texto el 85.0% del video.
- Resaltado de color en el 26.0% del tiempo · `#9E3F5A` `#366BC5` `#376CB6` `#366BCA` · tinta `#FEFCF9` `#FFFEFF` `#FDFEFE` `#FEFDFE`

## Voz

- **2.65 palabras por segundo** (estimada por subtítulos).

## Sonido

- -14.2 LUFS · **54.6 golpes/min** · 22.1% de cortes con golpe · voz 52.7% del tiempo · música de fondo: [False, False, False, False]
- Tipos: whoosh 115, golpe 93, pop/click 75

## Qué copiar y qué mejorar

**Copiar (identidad):** paleta y fondos, tipo de subtítulo, transiciones y movimientos más usados, mapa de sonido.

**Mejorar ([mejora] en la guía):**
- Primer cambio de escena antes de 4 s (el original da 6.66).
- Golpe de sonido en ≥ 80 % de los cortes (el original da 22.07).

## Siguiente paso: afinar con storyboards

```bash
python3 storyboard.py esqueleto gramatica.json --duracion 75 --n 3   # 3 storyboards nuevos con la gramática
python3 storyboard.py puntuar gramatica.json sb_*.json ref*/storyboard.json   # ranking y qué corregir
```

## Por referencia

- **De adolescente te CORTABAS las cejas..#cejas #datos #maquill** → `ref1_De_adolescente_te_CORTABAS_las/` · 82.59 s · 15 planos · 28.4 eventos/min · 58.4 s
- **Las legañas no te salen solo de noche, lo que pasa es que de** → `ref2_Las_legañas_no_te_salen/` · 65.94 s · 13 planos · 18.2 eventos/min · 55.6 s
- **¿Alguna vez te preguntaste cómo llega la música a tus audífo** → `ref3_Alguna_vez_te_preguntaste_cómo/` · 72.72 s · 16 planos · 33.9 eventos/min · 59.5 s
- **¿Por qué se te duerme la pierna y luego sientes hormigas Tu ** → `ref4_Por_qué_se_te_duerme/` · 90.53 s · 18 planos · 18.6 eventos/min · 58.7 s
