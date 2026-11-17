#!/usr/bin/env python3
"""
importar_estilo.py v2 · Drop Nation · Skill Motion
Baja un estilo de animación desde el GitHub de Drop Nation, liviano y rápido:
solo los archivos de ESE estilo, solo lo necesario para hacer videos y solo lo
que cambió desde la última vez.

Uso (alumno; lo corre Claude):
    python3 importar_estilo.py --lista
    python3 importar_estilo.py <id>    "<Tienda> - Claude/Bases/Skill Motion Graphics"
    python3 importar_estilo.py todos   "<Tienda> - Claude/Bases/Skill Motion Graphics"
Opciones:
    --demo       suma el video demo del estilo (ejemplo/)
    --completo   suma también Referencias/ y Estudio/ (para afinar o rehacer el estilo)
    --forzar     vuelve a bajar todo aunque ya esté al día

Uso (Paolo, antes de subir cambios al repo):
    python3 importar_estilo.py --generar-indice <carpeta estilos-motion>
    (actualiza indice.json con la lista de archivos, su tamaño y su huella)

Qué baja cada modo (de un estilo):
    base      Guía, estilo.json (con la gramática), plantilla/, Storyboards/  (< 1 MB)
    --demo    + ejemplo/                                                   (+ unos MB)
    --completo+ Referencias/ y Estudio/                                    (+ decenas de MB)
Siempre deja las Herramientas/ al día. Conserva "Notas del alumno.md".
Solo usa la biblioteca estándar de Python (Mac y Windows).
"""
import hashlib, io, json, sys, time, urllib.parse, urllib.request, zipfile
from pathlib import Path

REPO = "dropnationlatam/SKILLS-DROP-NATION"
RAMA = "main"
CARPETA = "estilos-motion"
RAW = f"https://raw.githubusercontent.com/{REPO}/{RAMA}/{CARPETA}/"
ZIP_URL = f"https://codeload.github.com/{REPO}/zip/refs/heads/{RAMA}"
EXTRA = {"Referencias": "completo", "Estudio": "completo", "ejemplo": "demo"}
VERSION = "2.0.0"


def bajar(url, intentos=3):
    for k in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "drop-nation-motion", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:
            if k == intentos - 1:
                raise
            time.sleep(1.5 * (k + 1))


def raw(ruta):
    return RAW + urllib.parse.quote(ruta)


def huella(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def mb(n):
    return "0 KB" if n == 0 else (f"{n/1e6:.1f} MB" if n >= 1e5 else f"{max(1, round(n/1e3))} KB")


def categoria(rel):
    return EXTRA.get(rel.split("/")[0], "base")


# ---------------------------------------------------------------- índice (Paolo)
def generar_indice(carpeta):
    base = Path(carpeta).expanduser()
    p = base / "indice.json"
    idx = json.loads(p.read_text()) if p.exists() else {"repo": REPO, "estilos": []}
    por_id = {e["id"]: e for e in idx.get("estilos", [])}
    estilos = []
    for d in sorted(x for x in base.iterdir() if x.is_dir() and (x / "estilo.json").exists()):
        ej = json.loads((d / "estilo.json").read_text())
        e = por_id.get(d.name, {})
        e.update({"id": d.name, "nombre": ej.get("nombre", e.get("nombre", d.name)), "version": ej.get("version", "1.0.0")})
        e.setdefault("descripcion", "")
        archivos = []
        for f in sorted(x for x in d.rglob("*") if x.is_file() and not x.name.startswith(".") and "__pycache__" not in x.parts):
            rel = f.relative_to(d).as_posix()
            archivos.append({"ruta": rel, "bytes": f.stat().st_size, "huella": huella(f), "tipo": categoria(rel)})
        e["archivos"] = archivos
        e["peso"] = {t: sum(a["bytes"] for a in archivos if a["tipo"] == t) for t in ("base", "demo", "completo")}
        estilos.append(e)
    h = base / "herramientas"
    idx["herramientas"] = [{"ruta": f.name, "bytes": f.stat().st_size, "huella": huella(f)}
                           for f in sorted(h.iterdir()) if f.is_file() and not f.name.startswith(".")] if h.exists() else []
    idx["estilos"] = estilos
    idx["formato_indice"] = 2
    idx["actualizado"] = time.strftime("%Y-%m-%d")
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    for e in estilos:
        print(f"✓ {e['id']} v{e['version']}: base {mb(e['peso']['base'])} · demo {mb(e['peso']['demo'])} · completo {mb(e['peso']['completo'])}")
    print(f"✓ Herramientas: {len(idx['herramientas'])} archivos → {p}")


# ---------------------------------------------------------------- alumno
def indice():
    return json.loads(bajar(RAW + "indice.json"))


def lista():
    idx = indice()
    for e in idx["estilos"]:
        peso = e.get("peso") or {}
        extra = f" · base {mb(peso.get('base', 0))}, con demo {mb(peso.get('base', 0) + peso.get('demo', 0))}" if peso else ""
        print(f"- {e['id']}: {e['nombre']} (v{e['version']}){extra} — {e.get('descripcion', '')}")


def sincronizar(archivos, url_de, destino, etiqueta, forzar):
    """baja solo los archivos que faltan o cambiaron (por huella)"""
    nuevos, bytes_ = 0, 0
    for a in archivos:
        out = destino / a["ruta"]
        if not forzar and out.exists() and out.stat().st_size == a["bytes"] and huella(out) == a["huella"]:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        data = bajar(url_de(a["ruta"]))
        tmp = out.with_name(out.name + ".bajando")
        tmp.write_bytes(data)
        tmp.replace(out)
        nuevos += 1
        bytes_ += len(data)
    print(f"✓ {etiqueta}: {nuevos} archivo(s) nuevos o cambiados ({mb(bytes_)})" if nuevos else f"✓ {etiqueta}: ya estaba al día")
    return bytes_


def importar(ids, destino, modo, forzar):
    destino = Path(destino).expanduser()
    try:
        idx = indice()
    except Exception as e:
        print(f"No pude leer el índice ({type(e).__name__}); uso el método antiguo (zip completo).")
        return importar_zip(ids, destino, modo)
    if idx.get("formato_indice", 1) < 2:
        print("El índice del repo es antiguo; uso el método antiguo (zip completo).")
        return importar_zip(ids, destino, modo)
    por_id = {e["id"]: e for e in idx["estilos"]}
    if ids == ["todos"]:
        ids = list(por_id)
    tipos = {"base"} | ({"demo"} if modo in ("demo", "completo") else set()) | ({"completo"} if modo == "completo" else set())
    total = 0
    for i in ids:
        e = por_id.get(i)
        if not e:
            print(f"✗ No existe el estilo '{i}'. Disponibles: {', '.join(por_id)}")
            continue
        dst = destino / "Estilos" / e["nombre"]
        local = dst / "estilo.json"
        quiere = [a for a in e["archivos"] if a["tipo"] in tipos]
        if not forzar and local.exists():
            try:
                if json.loads(local.read_text()).get("version") == e["version"] and all((dst / a["ruta"]).exists() for a in quiere):
                    print(f"✓ '{e['nombre']}' v{e['version']} ya está al día")
                    continue
            except Exception:
                pass
        dst.mkdir(parents=True, exist_ok=True)
        total += sincronizar(quiere, lambda r, i=i: raw(f"{i}/{r}"), dst, f"Estilo '{e['nombre']}' v{e['version']} ({modo})", forzar)
        print(f"  → {dst}")
    total += sincronizar(idx.get("herramientas", []), lambda r: raw(f"herramientas/{r}"), destino / "Herramientas", "Herramientas", forzar)
    print(f"Listo. Bajado en total: {mb(total)}")


def importar_zip(ids, destino, modo):
    z = zipfile.ZipFile(io.BytesIO(bajar(ZIP_URL)))
    raiz = z.namelist()[0].split("/")[0]
    idx = json.loads(z.read(f"{raiz}/{CARPETA}/indice.json"))
    por_id = {e["id"]: e for e in idx["estilos"]}
    if ids == ["todos"]:
        ids = list(por_id)
    for i in ids:
        if i not in por_id:
            print(f"✗ No existe el estilo '{i}'."); continue
        dst = destino / "Estilos" / por_id[i]["nombre"]
        pref = f"{raiz}/{CARPETA}/{i}/"
        for n in z.namelist():
            if n.startswith(pref) and not n.endswith("/"):
                rel = n[len(pref):]
                t = categoria(rel)
                if t == "completo" and modo != "completo" or t == "demo" and modo == "base":
                    continue
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                (dst / rel).write_bytes(z.read(n))
        print(f"✓ Estilo '{por_id[i]['nombre']}' → {dst}")
    pref = f"{raiz}/{CARPETA}/herramientas/"
    for n in z.namelist():
        if n.startswith(pref) and not n.endswith("/"):
            (destino / "Herramientas" / n[len(pref):]).parent.mkdir(parents=True, exist_ok=True)
            (destino / "Herramientas" / n[len(pref):]).write_bytes(z.read(n))
    print(f"✓ Herramientas al día → {destino / 'Herramientas'}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    if a[0] == "--lista":
        lista(); return
    if a[0] == "--generar-indice":
        generar_indice(a[1] if len(a) > 1 else "."); return
    flags = {x for x in a if x.startswith("--")}
    pos = [x for x in a if not x.startswith("--")]
    if len(pos) < 2:
        sys.exit("Falta la carpeta 'Skill Motion Graphics' de la tienda.")
    modo = "completo" if "--completo" in flags else ("demo" if "--demo" in flags else "base")
    importar(pos[0].split(","), pos[1], modo, "--forzar" in flags)


if __name__ == "__main__":
    main()
