# Comparación referencia vs nuestro

Referencia: `¿Por qué se te duerme la pierna y luego sientes hormigas Tu pierna no está dormida- está descone.mp4` · Nuestro: `demo.mp4`

| Medida | Referencia | Nuestro | Diferencia | Regla | ¿Pasa? |
|---|---|---|---|---|---|
| brillo | 23.6 | 15.8 | -7.8 | ±8 | ✅ |
| contraste | 17.9 | 15.0 | -2.9 | ±6 | ✅ |
| saturacion | 58.4 | 66.9 | +8.5 | ±10 | ✅ |
| temperatura | -15.6 | -21.3 | -5.7 | ±5 | ❌ |
| camara_viva_pct | 88.2 | 100.0 | +11.8 | ±15 | ✅ |
| golpes_por_min | 53.1 | 35.5 | -17.6 | ±15 | ❌ |
| lufs | -14.2 | -21.4 | -7.2 | ±2 | ❌ |
| plano_medio_s | 5.3 | 4.5 | -0.8 | superar (menor que la ref.) | ✅ |
| cortes_por_min | 10.6 | 8.9 | -1.7 | superar (mayor que la ref.) | ❌ |
| cortes_con_golpe_pct | 37.5 | 0.0 | -37.5 | superar (mayor que la ref.) | ❌ |

**Pasa 5 de 10.** Mira `lado_a_lado.jpg`: lo que no se mide (trazo, materiales, tipografía) se juzga a ojo.

Si algo falla: corrige ese valor en el proyecto, renderiza y vuelve a comparar (máximo 2 vueltas).
