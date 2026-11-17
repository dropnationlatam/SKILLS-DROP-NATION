# Puntaje de storyboards

Total = 40 % fidelidad al estilo + 40 % retención + 20 % movimiento de cámara.

| # | Storyboard | Total | Fidelidad | Retención | Movimiento | Planos | Plano mediano | Algo nuevo cada | SFX/min | Cortes con golpe |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sb/sb_3_cine.json cine | **93.6** | 84.0 | 100 | 100 | 20 | 3.83 s | 1.56 s | 54 | 100% |
| 2 | sb/sb_2_dinamica.json dinamica | **92.8** | 82.0 | 100 | 100 | 33 | 2.35 s | 1.36 s | 54 | 100% |
| 3 | sb/sb_1_fiel.json fiel | **86.9** | 84.8 | 100 | 65 | 25 | 2.89 s | 1.5 s | 54 | 100% |
| 4 | ref2_Las_legañas_no_te_salen/storyboard.json  | **69.7** | 84.2 | 40 | 100 | 13 | 3.3 s | 2.0 s | 52 | 33% |
| 5 | ref3_Alguna_vez_te_preguntaste_cómo/storyboard.json  | **68.3** | 78.3 | 55 | 75 | 16 | 2.87 s | 1.28 s | 63 | 27% |
| 6 | ref4_Por_qué_se_te_duerme/storyboard.json  | **61.8** | 82.0 | 40 | 65 | 18 | 4.97 s | 1.97 s | 55 | 29% |
| 7 | ref1_De_adolescente_te_CORTABAS_las/storyboard.json  | **59.7** | 76.7 | 40 | 65 | 15 | 4.63 s | 1.53 s | 49 | 21% |

## Qué corregir

**sb/sb_3_cine.json** (93.6)

- Nada: está listo.

**sb/sb_2_dinamica.json** (92.8)

- Nada: está listo.

**sb/sb_1_fiel.json** (86.9)

- 12% de planos con cámara quieta: dale deriva o empujón.

**ref2_Las_legañas_no_te_salen/storyboard.json** (69.7)

- Nada cambia antes de 0,8 s (primer cambio a los 4.1 s): agrega una transformación en el plano 1.
- El primer corte llega a los 4.1 s: corta el gancho antes de los 4 s.
- Solo el 33% de los cortes tiene sonido: pon whoosh/impacto en cada corte.
- Tramos sin nada nuevo de más de 2,6 s: 0.0-4.1 s, 4.1-7.0 s, 7.0-10.3 s, 10.6-15.5 s.

**ref3_Alguna_vez_te_preguntaste_cómo/storyboard.json** (68.3)

- El primer corte llega a los 4.1 s: corta el gancho antes de los 4 s.
- Solo el 27% de los cortes tiene sonido: pon whoosh/impacto en cada corte.
- Tramos sin nada nuevo de más de 2,6 s: 15.6-18.5 s, 28.3-33.6 s, 37.9-46.8 s, 60.7-67.5 s.
- Hay 3 planos seguidos con el mismo movimiento: alterna acercar/alejar/panear.

**ref4_Por_qué_se_te_duerme/storyboard.json** (61.8)

- El primer corte llega a los 7.2 s: corta el gancho antes de los 4 s.
- Plano mediano de 5.0 s: lleva los planos a 2-4,5 s.
- Solo el 29% de los cortes tiene sonido: pon whoosh/impacto en cada corte.
- Tramos sin nada nuevo de más de 2,6 s: 1.3-6.3 s, 11.7-17.9 s, 22.3-26.9 s, 27.4-30.3 s.
- 22% de planos con cámara quieta: dale deriva o empujón.

**ref1_De_adolescente_te_CORTABAS_las/storyboard.json** (59.7)

- El primer corte llega a los 11.3 s: corta el gancho antes de los 4 s.
- Plano mediano de 4.6 s: lleva los planos a 2-4,5 s.
- Solo el 21% de los cortes tiene sonido: pon whoosh/impacto en cada corte.
- Tramos sin nada nuevo de más de 2,6 s: 7.8-11.0 s, 11.6-15.9 s, 18.3-22.0 s, 27.0-37.3 s.
- 27% de planos con cámara quieta: dale deriva o empujón.

