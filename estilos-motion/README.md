# Estilos de animación · Skill Motion de Drop Nation

Estilos listos para la skill **motion-drop-nation**. Cada estilo trae su guía, sus números medidos, una plantilla de HyperFrames que ya funciona, un video demo, las referencias originales y el estudio completo.

## Para el alumno (lo hace Claude por ti)

Dile a Claude: **"importa el estilo Explicador Ilustrado"** (o "muéstrame los estilos"). Claude corre:
```bash
python3 "<Tienda> - Claude/Bases/Skill Motion Graphics/Herramientas/importar_estilo.py" explicador-ilustrado "<Tienda> - Claude/Bases/Skill Motion Graphics"
```
La primera vez, si no existe `Herramientas/`, Claude baja primero el script desde:
`https://raw.githubusercontent.com/dropnationlatam/SKILLS-DROP-NATION/main/estilos-motion/herramientas/importar_estilo.py`

## Estructura

```
estilos-motion/
├── indice.json                      lista de estilos (id, nombre, versión)
├── herramientas/
│   ├── importar_estilo.py           baja e instala estilos en un paso
│   ├── extraer_estilo.py            Fase A: mide todo de los mp4, saca la gramática y el storyboard real de cada uno
│   ├── storyboard.py                Fase E2: genera, puntúa y afina storyboards del estilo
│   ├── comparar.py                  Fase D: referencia vs clon en números
│   ├── generar_sfx.py               crea los efectos de sonido por código
│   ├── Proceso de extracción.md     el método completo (7 fases)
│   └── requirements.txt
└── <id-del-estilo>/
    ├── Guía de estilo.md
    ├── estilo.json
    ├── plantilla/                   proyecto HyperFrames (index.html + assets/)
    ├── ejemplo/demo.mp4
    ├── Estudio/                     informe, gramática, lectura, storyboard real y hojas de cada referencia
    ├── Storyboards/                 storyboards generados + puntaje
    └── Referencias/                 mp4 originales
```

## Para Paolo: sumar un estilo nuevo

1. Con la skill: "crea un estilo nuevo con estos mp4" → sigue `herramientas/Proceso de extracción.md`.
2. Copia la carpeta del estilo aquí como `estilos-motion/<id>/`.
3. Suma su línea en `indice.json` y sube los cambios.
4. Los alumnos lo traen con "importa el estilo <nombre>" o "actualiza los estilos".
