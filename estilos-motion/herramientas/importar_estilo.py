#!/usr/bin/env python3
"""
importar_estilo.py · Drop Nation · Skill Motion
Baja un estilo de animación desde el GitHub de Drop Nation y lo deja listo en la
carpeta de estilos del alumno, en un paso. También trae/actualiza las herramientas.

Uso:
    python3 importar_estilo.py --lista
    python3 importar_estilo.py <id-del-estilo> "<Tienda> - Claude/Bases/Skill Motion Graphics"
    python3 importar_estilo.py todos           "<Tienda> - Claude/Bases/Skill Motion Graphics"

Resultado:
    <Skill Motion Graphics>/Estilos/<Nombre del estilo>/   (guía, estilo.json, plantilla, ejemplo, referencias)
    <Skill Motion Graphics>/Herramientas/                  (extraer_estilo.py, comparar.py, generar_sfx.py, este script)
Si el estilo ya existía se reemplaza por la última versión, pero se conserva
"Notas del alumno.md" si el alumno lo tenía.
Solo usa la biblioteca estándar de Python (funciona en Mac y Windows).
"""
import io, json, shutil, sys, urllib.request, zipfile
from pathlib import Path

REPO = "dropnationlatam/SKILLS-DROP-NATION"
RAMA = "main"
CARPETA = "estilos-motion"
ZIP_URL = f"https://codeload.github.com/{REPO}/zip/refs/heads/{RAMA}"
RAW = f"https://raw.githubusercontent.com/{REPO}/{RAMA}/{CARPETA}/indice.json"


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "drop-nation-motion"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def lista():
    idx = json.loads(bajar(RAW))
    for e in idx["estilos"]:
        print(f"- {e['id']}: {e['nombre']} (v{e['version']}) — {e['descripcion']}")
    return idx


def importar(ids, destino):
    destino = Path(destino).expanduser()
    print("Bajando el repositorio de Drop Nation…")
    z = zipfile.ZipFile(io.BytesIO(bajar(ZIP_URL)))
    raiz = z.namelist()[0].split("/")[0]
    idx = json.loads(z.read(f"{raiz}/{CARPETA}/indice.json"))
    por_id = {e["id"]: e for e in idx["estilos"]}
    if ids == ["todos"]:
        ids = list(por_id)
    for i in ids:
        if i not in por_id:
            print(f"✗ No existe el estilo '{i}'. Disponibles: {', '.join(por_id)}"); continue
        e = por_id[i]
        dst = destino / "Estilos" / e["nombre"]
        notas = (dst / "Notas del alumno.md").read_text() if (dst / "Notas del alumno.md").exists() else None
        if dst.exists():
            shutil.rmtree(dst)
        pref = f"{raiz}/{CARPETA}/{i}/"
        for n in z.namelist():
            if n.startswith(pref) and not n.endswith("/"):
                out = dst / n[len(pref):]
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(n))
        if notas:
            (dst / "Notas del alumno.md").write_text(notas)
        print(f"✓ Estilo '{e['nombre']}' v{e['version']} → {dst}")
    # herramientas compartidas
    pref = f"{raiz}/{CARPETA}/herramientas/"
    h = destino / "Herramientas"
    h.mkdir(parents=True, exist_ok=True)
    for n in z.namelist():
        if n.startswith(pref) and not n.endswith("/"):
            (h / n[len(pref):]).parent.mkdir(parents=True, exist_ok=True)
            (h / n[len(pref):]).write_bytes(z.read(n))
    print(f"✓ Herramientas al día → {h}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if a[0] == "--lista":
        lista(); return
    if len(a) < 2:
        print("Falta la carpeta 'Skill Motion Graphics' de la tienda."); sys.exit(1)
    importar(a[0].split(","), a[1])


if __name__ == "__main__":
    main()
