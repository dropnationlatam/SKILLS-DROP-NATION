#!/usr/bin/env python3
"""
extraer_estilo.py v2 · Drop Nation · Skill Motion
Mide TODO lo medible de uno o varios mp4 de referencia, rearma el storyboard real
de cada uno y saca la GRAMÁTICA del estilo (cómo se arma un video de ese estilo),
para clonarlo y después afinarlo con storyboard.py.

Uso:
    python3 extraer_estilo.py <carpeta_o_mp4> [salida] [opciones]

Opciones:
    --sin-ocr        no lee textos en pantalla (más rápido)
    --sin-voz        no transcribe la voz
    --rapido         menos muestras (para revisar un video final en segundos)
    --trabajos N     videos en paralelo (por defecto: núcleos disponibles)
    --forzar         vuelve a medir aunque ya exista un análisis guardado

Deja en <salida>/ (por defecto ./estudio):
    Informe de extracción.md   resumen + tabla de retención + qué copiar / qué mejorar
    gramatica.json             la gramática del estilo (la usa storyboard.py)
    resumen.json               números globales del estilo
    estilo.borrador.json       primer borrador de estilo.json (la Fase C parte aquí)
    <ref>/storyboard.json|.md  el storyboard real de la referencia, plano por plano
    <ref>/datos.json           todo lo medido de esa referencia
    <ref>/planos.jpg  gancho.jpg  eventos.jpg  subtitulos.jpg  linea_tiempo.png
    <ref>/transiciones/NN.jpg  mapa_actividad.jpg  planos/NNN.jpg

Requiere: ffmpeg/ffprobe, Python 3.9+, opencv-python, numpy, scikit-learn, pillow.
Opcional: scenedetect, pytesseract + tesseract con español, faster-whisper.
"""
import argparse, json, math, os, re, subprocess, sys, time, statistics as st
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from shutil import which

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

VERSION = "2.0.0"
AN_W = 180                       # ancho de análisis rápido
VID_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}

# Reglas de retención (Fase E): (clave, texto, decide si pasa)
RETENCION = [
    ("primer_cambio_visual_s", "Algo cambia en pantalla antes de 0,8 s", lambda v: v is not None and v <= 0.8),
    ("primer_corte_s", "Primer cambio de escena antes de 4 s", lambda v: v is not None and v <= 4.0),
    ("plano_mediana_s", "Plano mediano entre 2 y 4,5 s", lambda v: v is not None and 2.0 <= v <= 4.5),
    ("evento_cada_s", "Algo nuevo pasa cada ≤ 2 s (cortes + eventos)", lambda v: v is not None and v <= 2.0),
    ("subtitulo_alto_px", "Letra de subtítulo ≥ 46 px de alto a 1920 (≈ 64 px de cuerpo)", lambda v: v is None or v >= 46),
    ("zona_ui_pct", "Poca acción en el 12 % de abajo (interfaz de la app) ≤ 12 %", lambda v: v is not None and v <= 12),
    ("cortes_con_golpe_pct", "Golpe de sonido en ≥ 80 % de los cortes", lambda v: v is None or v >= 80),
    ("golpes_por_min", "Entre 40 y 70 efectos por minuto", lambda v: v is None or 40 <= v <= 70),
]


# ================================================================ utilidades
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def hexc(rgb):
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, c))) for c in rgb)


def slug(name, i):
    s = re.sub(r"[^\w ]+", "", Path(name).stem, flags=re.UNICODE).strip()
    return f"ref{i}_" + ("_".join(s.split()[:5]) or "ref")[:40]


def fuente(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def r2(x, n=2):
    return None if x is None else round(float(x), n)


def media(vals, n=2):
    vals = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return round(float(st.mean(vals)), n) if vals else None


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
             "-of", "json", str(path)])
    j = json.loads(r.stdout or "{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in j.get("streams", []))
    n, d = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    return {"ancho": v.get("width"), "alto": v.get("height"), "fps": round(float(n) / float(d or 1), 3),
            "duracion": round(float(j.get("format", {}).get("duration", 0) or 0), 2), "tiene_audio": a}


def picos(serie, umbral, sep):
    """máximos locales sobre el umbral, separados por al menos `sep` muestras (gana el más alto)"""
    s = np.asarray(serie)
    if len(s) < 3:
        return []
    cand = np.flatnonzero((s[1:-1] > umbral) & (s[1:-1] >= s[:-2]) & (s[1:-1] >= s[2:])) + 1
    out = []
    for i in cand[np.argsort(-s[cand])]:
        if all(abs(i - j) >= sep for j in out):
            out.append(int(i))
    return sorted(out)


# ================================================================ lectura: 2 pasadas secuenciales (sin saltos = rápido)
def pasada_chica(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    small = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h, w = f.shape[:2]
        small.append(cv2.resize(f, (AN_W, int(h * AN_W / w)), interpolation=cv2.INTER_AREA))
    cap.release()
    return np.array(small), fps


def pasada_grande(path, indices, banda=None, banda_cada=1):
    """{índice: cuadro completo} de los índices pedidos + la franja `banda` (y0, y1) a 360 px cada `banda_cada` cuadros"""
    cap = cv2.VideoCapture(str(path))
    quiero, full, bandas, i = set(indices), {}, {}, 0
    ultimo = max(quiero) if quiero else -1
    while True:
        if not banda and i > ultimo:
            break
        ok = cap.grab()
        if not ok:
            break
        if i in quiero or (banda and i % banda_cada == 0):
            ok, f = cap.retrieve()
            if ok:
                if i in quiero:
                    full[i] = f
                if banda and i % banda_cada == 0:
                    h, w = f.shape[:2]
                    crop = f[int(banda[0] * h):int(banda[1] * h)]
                    bandas[i] = cv2.resize(crop, (360, max(8, int(crop.shape[0] * 360 / w))), interpolation=cv2.INTER_AREA)
        i += 1
    cap.release()
    return full, bandas


# ================================================================ cortes, eventos, transiciones
def energia(frames, fps):
    """cambio de imagen (0-100) mirando 0,1 s atrás: total y por zona (grilla 4x6),
    para ver también lo que cambia en un rincón (una etiqueta que aparece, un ícono)"""
    g = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]).astype(np.int16)
    k = max(1, int(round(fps / 10)))
    d = np.zeros(g.shape, np.float32)
    d[k:] = np.abs(g[k:] - g[:-k])
    e = d.mean(axis=(1, 2)) / 2.55
    H, W = g.shape[1:]
    gy, gx = 6, 4
    hh, ww = H // gy, W // gx
    zonas = d[:, :hh * gy, :ww * gx].reshape(len(g), gy, hh, gx, ww).mean(axis=(2, 4)) / 2.55
    return e, zonas.reshape(len(g), -1)


def detectar_cortes(frames, fps):
    hsv = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
    hist = [cv2.normalize(cv2.calcHist([h], [0, 1], None, [24, 16], [0, 180, 0, 256]), None).flatten() for h in hsv]
    f16 = frames.astype(np.int16)
    pd = np.r_[0, np.abs(f16[1:] - f16[:-1]).mean(axis=(1, 2, 3)) / 255]
    hd = np.r_[0, [cv2.compareHist(hist[i - 1], hist[i], cv2.HISTCMP_BHATTACHARYYA) for i in range(1, len(frames))]]
    diff = 0.6 * hd + 0.4 * pd * 3
    med = float(np.median(diff))
    thr = max(0.2, med + 6 * (float(np.median(np.abs(diff - med))) + 1e-6))
    cuts = picos(diff, thr, max(3, int(fps * 0.2)))
    reales, destellos = [], []
    for c in cuts:
        a, b = max(0, c - int(fps * 0.2)), min(len(frames) - 1, c + int(fps * 0.35))
        vuelve = np.mean(np.abs(f16[a] - f16[b])) < 6
        (destellos if vuelve and frames[c].mean() > 150 else reales).append(c)
    return reales, destellos, diff


def tipo_transicion(frames, diff, c, fps):
    w = max(2, int(fps * 0.25))
    seg = diff[max(1, c - w): min(len(diff), c + w + 1)]
    lum = [frames[i].mean() for i in range(max(0, c - w), min(len(frames), c + w))]
    if lum and (max(lum) > 225 or max(lum) - np.median(lum) > 70):
        return "destello"
    if lum and min(lum) < 18:
        return "paso por negro"

    def nit(i):
        return cv2.Laplacian(cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    s_cut = min(nit(max(0, c - 1)), nit(c))
    ref = [nit(i) for i in range(max(0, c - 2 * w), max(1, c - w))] or [s_cut]
    if np.median(ref) > 0 and s_cut < np.median(ref) * 0.35:
        return "barrido"
    try:
        a = cv2.cvtColor(frames[max(0, c - 3)], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[max(0, c - 1)], cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(a, 120, 0.01, 5)
        if p0 is not None and len(p0) > 8:
            p1, stt, _ = cv2.calcOpticalFlowPyrLK(a, b, p0, None)
            M, _ = cv2.estimateAffinePartial2D(p0[stt == 1], p1[stt == 1])
            if M is not None and math.hypot(M[0, 0], M[1, 0]) > 1.04:
                return "entrar con zoom"
    except Exception:
        pass
    if len(seg) and (seg > seg.max() * 0.45).sum() >= max(4, int(fps * 0.2)):
        return "fundido"
    return "corte seco"


def eventos_en_planos(e, zonas, cuts, destellos, fps, banda=None):
    """cambios fuertes DENTRO de un plano: algo aparece, se transforma, entra una etiqueta.
    Mira cada zona de la pantalla (grilla 4x6) contra su propio nivel normal; ignora la franja
    de subtítulos para no contar cada palabra como evento."""
    if banda:
        filas = [r for r in range(6) if not (r / 6 < banda[1] and (r + 1) / 6 > banda[0] + 0.02)]
        zonas = zonas.reshape(len(zonas), 6, 4)[:, filas, :].reshape(len(zonas), -1)
    med_z = np.median(zonas, axis=0) + 1.0
    rel = (zonas / med_z).max(axis=1)              # la zona que más se salió de lo normal
    fuerza = zonas.max(axis=1)
    señal = np.where(fuerza > 9, rel, 0)
    lejos = set()
    for c in list(cuts) + list(destellos):
        lejos.update(range(c - int(fps * 0.2), c + int(fps * 0.35)))
    return [p for p in picos(señal, 5.0, int(fps * 0.45)) if p not in lejos]


# ================================================================ cámara
def movimiento(frames, a, b, fps):
    step = max(1, int(round(fps / 10)))
    zs, txs, tys, rots, mags = [], [], [], [], []
    prev = cv2.cvtColor(frames[a], cv2.COLOR_BGR2GRAY)
    for i in range(a + step, b, step):
        cur = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(prev, 150, 0.01, 5)
        if p0 is not None and len(p0) > 8:
            p1, stt, _ = cv2.calcOpticalFlowPyrLK(prev, cur, p0, None)
            g0, g1 = p0[stt == 1], p1[stt == 1]
            if len(g0) > 8:
                M, _ = cv2.estimateAffinePartial2D(g0, g1)
                if M is not None:
                    zs.append(math.hypot(M[0, 0], M[1, 0])); txs.append(M[0, 2]); tys.append(M[1, 2])
                    rots.append(math.degrees(math.atan2(M[1, 0], M[0, 0])))
                    mags.append(float(np.mean(np.linalg.norm(g1 - g0, axis=1))))
        prev = cur
    if len(zs) < 2:
        return {"principal": "quieto", "tipo": "sin datos"}
    dt = step / fps
    T = len(zs) * dt
    k = 1080 / AN_W
    escala_total = float(np.prod(zs))
    z_rate = (escala_total ** (1 / max(1e-6, T)) - 1) * 100
    pan_x, pan_y = float(np.sum(txs)) * k, float(np.sum(tys)) * k
    rot = float(np.sum(rots))
    sac = float(np.std(np.diff(mags))) * k if len(mags) > 2 else 0.0
    # movimiento principal (normalizado: 4 % de escala ≈ 120 px de paneo ≈ 3° de giro)
    sc = {"zoom": abs(escala_total - 1) * 100 / 4, "paneo": math.hypot(pan_x, pan_y) / 120, "giro": abs(rot) / 3}
    top = max(sc, key=sc.get)
    if sc[top] < 1:
        principal = "deriva leve" if max(sc.values()) > 0.35 else "quieto"
    elif top == "zoom":
        principal = "acercamiento" if escala_total > 1 else "alejamiento"
    elif top == "paneo":
        principal = "paneo vertical" if abs(pan_y) > abs(pan_x) else "paneo horizontal"
    else:
        principal = "giro"
    tipos = [principal] + (["sacudida"] if sac > 25 else [])
    prog = np.cumsum(np.abs(np.log(np.array(zs))) * 50 + np.hypot(txs, tys))
    easing = "—"
    if prog[-1] > 1e-3 and len(prog) >= 5:
        p = prog / prog[-1]
        x = np.linspace(0, 1, len(p))
        cands = {"none": x, "power2.out": 1 - (1 - x) ** 3, "power2.in": x ** 3,
                 "sine.inOut": np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)}
        easing = min(cands, key=lambda c: float(np.mean((cands[c] - p) ** 2)))
    # valores listos para EI.camara (escala desde 1, desplazamiento en px de 1080)
    return {"principal": principal, "tipo": ", ".join(tipos), "zoom_pct_s": r2(z_rate),
            "escala": [1.0, r2(escala_total, 3)], "x_px": [0, round(-pan_x)], "y_px": [0, round(-pan_y)],
            "giro_grados": [0, r2(-rot, 1)], "sacudida": r2(sac, 1), "easing": easing}


# ================================================================ color
def paleta(imgs, k=8):
    from sklearn.cluster import KMeans
    px = np.concatenate([cv2.resize(i, (48, 85)).reshape(-1, 3) for i in imgs])
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)
    k = int(min(k, max(1, len(np.unique(lab[:2000], axis=0)))))
    km = KMeans(n_clusters=k, n_init=2, random_state=0).fit(lab)
    out = []
    for ci in np.argsort(-np.bincount(km.labels_)):
        bgr = cv2.cvtColor(km.cluster_centers_[ci].astype(np.uint8).reshape(1, 1, 3), cv2.COLOR_LAB2BGR)[0, 0]
        hsv = cv2.cvtColor(bgr.reshape(1, 1, 3), cv2.COLOR_BGR2HSV)[0, 0]
        s, v = int(hsv[1]), int(hsv[2])
        rol = "fondo" if v < 90 and s < 170 else ("acento" if s > 120 and v > 140 else "medio")
        out.append({"hex": hexc(bgr[::-1]), "pct": round(100 * float(np.mean(km.labels_ == ci)), 1), "rol": rol})
    return out


def color_medio(img):
    c = cv2.resize(img, (1, 1), interpolation=cv2.INTER_AREA)[0, 0]
    return hexc(c[::-1])


def acentos_vivos(imgs, n=6):
    """colores muy saturados y brillantes aunque ocupen poco (neones, cajas, flechas)"""
    px = np.concatenate([cv2.resize(i, (90, 160)).reshape(-1, 3) for i in imgs])
    hsv = cv2.cvtColor(px.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    m = (hsv[:, 1] > 150) & (hsv[:, 2] > 170)
    if m.sum() < 30:
        return []
    h = hsv[m, 0].astype(int) // 6
    hist = np.bincount(h, minlength=30)
    out = []
    for b in np.argsort(-hist)[:n]:
        if hist[b] >= m.sum() * 0.04:
            out.append({"hex": hexc(np.median(px[m][h == b], 0)[::-1]), "pct_de_acentos": round(100 * hist[b] / m.sum(), 1)})
    return out


def grading(imgs):
    lab = [cv2.cvtColor(i, cv2.COLOR_BGR2LAB).astype(float) for i in imgs]
    hsv = [cv2.cvtColor(i, cv2.COLOR_BGR2HSV).astype(float) for i in imgs]
    t = float(np.mean([l[..., 2].mean() - 128 for l in lab]))
    return {"brillo_medio": r2(np.mean([l[..., 0].mean() for l in lab]) / 2.55, 1),
            "contraste": r2(np.mean([l[..., 0].std() for l in lab]) / 2.55, 1),
            "saturacion_media": r2(np.mean([h[..., 1].mean() for h in hsv]) / 2.55, 1),
            "temperatura": r2(t, 1), "nota_temperatura": "cálido" if t > 4 else ("frío" if t < -4 else "neutro"),
            "negros_pct": r2(np.mean([(l[..., 0] < 25).mean() for l in lab]) * 100, 1)}


def actividad(frames, out):
    f = frames[::2].astype(np.int16)
    acc = np.abs(np.diff(f, axis=0)).mean(axis=(0, 3)).astype(float)
    acc = acc / (acc.max() + 1e-6)
    heat = cv2.applyColorMap(cv2.resize((acc * 255).astype(np.uint8), (360, int(360 * acc.shape[0] / acc.shape[1]))), cv2.COLORMAP_INFERNO)
    H = heat.shape[0]
    for p, c in ((10, (255, 255, 255)), (88, (0, 220, 255))):
        cv2.line(heat, (0, int(H * p / 100)), (360, int(H * p / 100)), c, 1)
    cv2.imwrite(str(out), heat)
    filas = acc.mean(1)
    s, n = filas.sum() + 1e-6, len(filas)
    return {"arriba_pct": round(100 * filas[: n // 3].sum() / s), "centro_pct": round(100 * filas[n // 3: 2 * n // 3].sum() / s),
            "abajo_pct": round(100 * filas[2 * n // 3:].sum() / s), "zona_ui_pct": round(100 * filas[int(n * 0.88):].sum() / s, 1)}


# ================================================================ textos
def ocr(full, fps, idxs):
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        return None
    langs = "spa+eng" if "spa" in run(["tesseract", "--list-langs"]).stdout else "eng"
    hits = []
    for i in idxs:
        f = full.get(i)
        if f is None:
            continue
        H, W = f.shape[:2]
        esc = 720 / W
        g = cv2.cvtColor(cv2.resize(f, (720, int(H * esc))), cv2.COLOR_BGR2GRAY)
        d = pytesseract.image_to_data(g, lang=langs, config="--psm 11", output_type=pytesseract.Output.DICT)
        for j, txt in enumerate(d["text"]):
            txt = txt.strip(" |_—-")
            if len(txt) < 2 or float(d["conf"][j]) < 72 or not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9]{2}", txt):
                continue
            x, y, w, h = [int(d[k][j] / esc) for k in ("left", "top", "width", "height")]
            box = f[y:y + h, x:x + w].reshape(-1, 3)
            if len(box) < 10:
                continue
            lum = box.mean(1)
            hits.append({"t": round(i / fps, 2), "texto": txt, "y_pct": round(100 * (y + h / 2) / H, 1),
                         "x_pct": round(100 * (x + w / 2) / W, 1), "alto_px_1920": round(h * 1920 / H),
                         "tinta": hexc(box[lum >= np.percentile(lum, 85)].mean(0)[::-1]), "mayus": txt.isupper()})
    return hits


def banda_subtitulos(hits):
    if not hits or len(hits) < 5:
        return None
    ys = np.array([h["y_pct"] for h in hits])
    b = int(np.argmax(np.bincount((ys // 4).astype(int), minlength=26)))
    sel = [h for h in hits if abs(h["y_pct"] - (b * 4 + 2)) <= 8]
    if len(sel) < max(4, 0.25 * len(hits)):
        return None
    yc = float(np.median([h["y_pct"] for h in sel]))
    alto = float(np.median([h["alto_px_1920"] for h in sel]))
    pad = max(5.0, alto / 19.2 * 2.6)
    return {"y_centro_pct": round(yc, 1), "y0": max(0.0, (yc - pad) / 100), "y1": min(1.0, (yc + pad) / 100),
            "alto_px_1920": round(alto), "lecturas": len(sel), "mayus_pct": round(100 * np.mean([h["mayus"] for h in sel])),
            "x_centro_pct": round(float(np.median([h["x_pct"] for h in sel])), 1)}


def analizar_banda(bandas, fps):
    """karaoke, cadencia de cambios y color de resaltado mirando solo los píxeles de la franja"""
    if not bandas:
        return None
    ks = sorted(bandas)
    B = np.array([bandas[k] for k in ks])
    hsv = np.array([cv2.cvtColor(b, cv2.COLOR_BGR2HSV) for b in B])
    s, v = hsv[..., 1], hsv[..., 2]
    blanco = ((v > 225) & (s < 40)).mean(axis=(1, 2))
    gris = ((v > 110) & (v < 190) & (s < 35)).mean(axis=(1, 2))
    vivo_m = (s > 150) & (v > 150)
    vivo = vivo_m.mean(axis=(1, 2))
    dif = np.r_[0, np.abs(np.diff(B.astype(np.int16), axis=0)).mean(axis=(1, 2, 3))]
    hay = blanco > 0.004
    paso = (ks[1] - ks[0]) if len(ks) > 1 else 1
    cambios = picos(dif, max(1.5, float(np.median(dif)) * 2.5), max(1, int(0.1 * fps / paso)))
    seg_texto = hay.sum() * paso / fps
    res = {"karaoke_pct": round(100 * float(np.mean((blanco > 0.004) & (gris > 0.004)) / max(1e-6, hay.mean()))) if hay.any() else 0,
           "texto_en_pantalla_pct": round(100 * float(hay.mean())),
           "cambios_por_s": round(len(cambios) / max(0.5, seg_texto), 2),
           "resaltado_pct": round(100 * float(np.mean(vivo > 0.003))),
           "cambios_t": [round(ks[c] / fps, 2) for c in cambios]}
    if vivo_m.any():
        res["resaltado_hex"] = hexc(np.median(B[vivo_m], 0)[::-1])
    return res


# ================================================================ audio
def audio(path, cuts_t, dur, carpeta):
    wav = carpeta / "audio.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", str(wav)])
    if not wav.exists():
        return None
    import wave
    with wave.open(str(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    sr, hop, win = 16000, 320, 1024
    if len(x) < win * 2:
        return None
    nfr = 1 + (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(win).astype(np.float32), axis=1))
    freqs = np.fft.rfftfreq(win, 1 / sr)
    pot = (S ** 2).sum(1) + 1e-12
    db = 10 * np.log10(pot / win) - 10
    voz_ratio = (S[:, (freqs > 300) & (freqs < 3400)] ** 2).sum(1) / pot
    p10, p50 = float(np.percentile(db, 10)), float(np.percentile(db, 50))
    voz = (db > p50 - 20) & (voz_ratio > 0.25)
    flux = np.r_[0, np.maximum(0, np.diff(S, axis=0)).sum(1)]
    cent = (S * freqs).sum(1) / (S.sum(1) + 1e-9)
    on = picos(flux, float(np.median(flux) + 3.0 * np.std(flux)), int(0.12 * sr / hop))
    golpes = []
    for i in on:
        j = i
        while j < len(db) - 1 and db[j] > db[i] - 12 and j - i < 60:
            j += 1
        d, c = (j - i) * hop / sr, float(cent[i])
        tipo = "grave/impacto" if c < 400 else ("whoosh" if d > 0.22 else ("pop/click" if c > 1500 else "golpe"))
        golpes.append({"t": round(i * hop / sr, 2), "tipo": tipo, "dura": round(d, 2)})
    tipos = {}
    for g in golpes:
        tipos[g["tipo"]] = tipos.get(g["tipo"], 0) + 1
    fondo = float(np.mean(db[~voz] > p50 - 30)) if (~voz).any() else 0.0
    lufs = None
    m = re.findall(r"I:\s+(-?\d+\.\d) LUFS", run(["ffmpeg", "-v", "info", "-i", str(path), "-af", "ebur128", "-f", "null", "-"]).stderr)
    if m:
        lufs = float(m[-1])
    t_on = np.array([g["t"] for g in golpes]) if golpes else np.array([])
    en_corte = sum(1 for c in cuts_t if len(t_on) and np.min(np.abs(t_on - c)) <= 0.1)
    cambios_voz = [round(i * hop / sr, 2) for i in np.flatnonzero(np.diff(voz.astype(int)) != 0)]
    return {"lufs": lufs, "golpes_por_min": round(len(golpes) / max(1, dur) * 60, 1), "golpes": golpes, "tipos_golpe": tipos,
            "cortes_con_golpe_pct": round(100 * en_corte / len(cuts_t), 1) if cuts_t else None,
            "voz_pct": round(100 * float(voz.mean()), 1), "silencio_pct": round(100 * float(np.mean(db < -50)), 1),
            "musica_fondo": p10 > p50 - 30, "fondo_pct": round(100 * fondo, 1), "voz_cambios": cambios_voz[:600], "wav": str(wav)}


def transcribir(wav):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return {"error": "sin faster-whisper: la cadencia de la voz se estima desde los subtítulos"}
    try:
        m = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
        segs, _ = m.transcribe(wav, language="es", word_timestamps=True, vad_filter=True)
        words, texto = [], []
        for s in segs:
            texto.append(s.text.strip())
            words += [{"p": w.word.strip(), "i": round(w.start, 2), "f": round(w.end, 2)} for w in (s.words or [])]
        if not words:
            return None
        habla = sum(w["f"] - w["i"] for w in words)
        frases = re.split(r"(?<=[.?!])\s+", " ".join(texto))
        return {"texto": " ".join(texto), "palabras": words,
                "palabras_por_seg": round(len(words) / max(0.1, words[-1]["f"] - words[0]["i"]), 2),
                "palabras_por_seg_hablando": round(len(words) / max(0.1, habla), 2),
                "primera_palabra_s": words[0]["i"], "gancho_3s": " ".join(w["p"] for w in words if w["i"] < 3.0),
                "cierre": frases[-1] if frases else "", "preguntas": sum(1 for f in frases if "?" in f)}
    except Exception as e:
        return {"error": f"no se pudo transcribir ({type(e).__name__}); revisa la red para bajar el modelo"}


# ================================================================ imágenes
def hoja(imgs, labels, cols, out, w=240):
    pares = [(i, l) for i, l in zip(imgs, labels) if i is not None]
    if not pares:
        return
    h = int(pares[0][0].shape[0] * w / pares[0][0].shape[1])
    rows = math.ceil(len(pares) / cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + 26)), (18, 18, 22))
    d, f = ImageDraw.Draw(sheet), fuente(15)
    for n, (im, lb) in enumerate(pares):
        r, c = divmod(n, cols)
        sheet.paste(Image.fromarray(cv2.cvtColor(cv2.resize(im, (w, h)), cv2.COLOR_BGR2RGB)), (c * w, r * (h + 26) + 26))
        d.text((c * w + 5, r * (h + 26) + 5), lb, fill=(255, 214, 0), font=f)
    sheet.save(out, quality=86)


def linea_tiempo(dur, cuts_t, eventos_t, golpes, voz_cambios, subs_t, out):
    W, H = 1600, 230
    im = Image.new("RGB", (W, H), (18, 18, 22))
    d, f = ImageDraw.Draw(im), fuente(14)
    X = lambda t: int(70 + (W - 90) * t / max(dur, 0.1))
    for nombre, y, c in [("cortes", 30, (255, 214, 0)), ("eventos", 70, (67, 217, 255)), ("sonido", 110, (255, 63, 164)),
                         ("voz", 150, (61, 255, 168)), ("subtít.", 190, (200, 200, 210))]:
        d.text((4, y - 8), nombre, fill=c, font=f)
        d.line([(70, y), (W - 20, y)], fill=(50, 50, 60))
    for t in cuts_t: d.line([(X(t), 18), (X(t), 42)], fill=(255, 214, 0), width=3)
    for t in eventos_t: d.ellipse([X(t) - 4, 66, X(t) + 4, 74], fill=(67, 217, 255))
    for g in golpes: d.line([(X(g["t"]), 100), (X(g["t"]), 120)], fill=(255, 63, 164), width=2)
    for k in range(0, len(voz_cambios) - 1, 2):
        d.rectangle([X(voz_cambios[k]), 145, X(voz_cambios[k + 1]), 155], fill=(61, 255, 168))
    for t in subs_t: d.line([(X(t), 184), (X(t), 196)], fill=(200, 200, 210), width=1)
    for s in range(0, int(dur) + 1, 5):
        d.text((X(s) - 6, H - 18), f"{s}s", fill=(120, 120, 130), font=f)
    im.save(out)


# ================================================================ storyboard real de la referencia
def recurso_de_golpe(tipo):
    return {"whoosh": "whoosh", "pop/click": "pop", "grave/impacto": "impacto", "golpe": "tick"}.get(tipo, "tick")


def storyboard_inverso(dt):
    """el video de referencia escrito como storyboard (mismo formato que storyboard.py)"""
    hits = ((dt.get("textos") or {}).get("lecturas") or [])
    banda = ((dt.get("textos") or {}).get("subtitulos") or {})
    golpes = ((dt.get("audio") or {}).get("golpes") or [])
    palabras = ((dt.get("voz") or {}).get("palabras") or [])
    planos = []
    for p in dt["planos"]:
        a, b = p["inicio"], p["fin"]
        if palabras:
            texto = " ".join(w["p"] for w in palabras if a <= w["i"] < b)
        else:
            vistos = []
            for h in hits:
                if a <= h["t"] < b and (not banda or abs(h["y_pct"] - banda.get("y_centro_pct", 0)) <= 8) and h["texto"] not in vistos:
                    vistos.append(h["texto"])
            texto = " ".join(vistos)
        etiquetas = sorted({h["texto"] for h in hits if a <= h["t"] < b and banda and abs(h["y_pct"] - banda.get("y_centro_pct", 0)) > 9})
        cam = p["camara"]
        planos.append({"n": p["n"], "inicio": a, "dura": p["dura"], "transicion_entrada": p["transicion_entrada"],
                       "camara": {"mov": cam.get("principal", "quieto"), "escala": cam.get("escala"), "x_px": cam.get("x_px"),
                                  "y_px": cam.get("y_px"), "giro_grados": cam.get("giro_grados"), "ease": cam.get("easing"),
                                  "sacudida": "sacudida" in cam.get("tipo", "")},
                       "eventos": [{"t": t, "tipo": "COMPLETAR"} for t in dt["eventos_t"] if a <= t < b],
                       "sfx": [{"t": g["t"], "sonido": recurso_de_golpe(g["tipo"])} for g in golpes if a <= g["t"] < b],
                       "texto_voz": texto, "etiquetas": etiquetas[:4],
                       "que_se_ve": f"COMPLETAR (mirar planos/{p['n']:03d}.jpg)", "color": p.get("color")})
    return {"titulo": dt["archivo"], "tipo": "referencia", "duracion_s": dt["meta"]["duracion"], "planos": planos}


def storyboard_md(sb):
    L = [f"# Storyboard · {sb['titulo']}", "", f"{len(sb['planos'])} planos · {sb['duracion_s']} s", "",
         "| # | Inicio | Dura | Entra con | Cámara | Eventos | Sonidos | Voz / texto | Qué se ve |", "|---|---|---|---|---|---|---|---|---|"]
    for p in sb["planos"]:
        c = p["camara"]
        cam = c["mov"]
        if c.get("escala") and c["escala"][1] and abs(c["escala"][1] - 1) > 0.015:
            cam += f" {c['escala'][0]}→{c['escala'][1]}"
        if c.get("sacudida"):
            cam += " + sacudida"
        L.append(f"| {p['n']} | {p['inicio']} | {p['dura']} | {p['transicion_entrada']} | {cam} ({c.get('ease','—')}) | "
                 f"{len(p['eventos'])} | {', '.join(s['sonido'] for s in p['sfx']) or '—'} | {p.get('texto_voz','')[:70]} | {p.get('que_se_ve','')} |")
    return "\n".join(L) + "\n"


# ================================================================ una referencia
def clave_cache(path, opts):
    s = path.stat()
    return f"{s.st_size}-{int(s.st_mtime)}-{VERSION}-{int(opts['sin_ocr'])}{int(opts['sin_voz'])}{int(opts['rapido'])}"


def analizar(args):
    path, outdir, idx, opts = args
    t0 = time.time()
    path, outdir = Path(path), Path(outdir)
    d = outdir / slug(path.name, idx)
    clave = clave_cache(path, opts)
    if not opts["forzar"] and (d / "datos.json").exists():
        try:
            prev = json.loads((d / "datos.json").read_text())
            if prev.get("clave") == clave:
                prev["segundos_analisis"] = 0.0
                return str(d), prev
        except Exception:
            pass
    for sub in ("planos", "transiciones"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    meta = probe(path)
    frames, fps = pasada_chica(path)
    n = len(frames)
    dur = n / fps
    e, zonas = energia(frames, fps)
    cuts, destellos, diff = detectar_cortes(frames, fps)
    bounds = [0] + cuts + [n]

    mids = [(a + b) // 2 for a, b in zip(bounds, bounds[1:]) if b - a >= 2]
    hook = sorted({min(n - 1, int(t * fps / 10)) for t in range(30)})
    trans = {c: [max(0, min(n - 1, c + int(dt_ * fps))) for dt_ in (-0.3, -0.2, -0.1, -0.033, 0, 0.1, 0.2, 0.3)] for c in cuts[:60]}
    cada = 2.0 if opts["rapido"] else 1.0
    ocr_idx = sorted({min(n - 1, int(k * cada * fps)) for k in range(int(dur / cada))})
    pedir = set(mids) | set(hook) | {i for v in trans.values() for i in v}
    if not opts["sin_ocr"]:
        pedir |= set(ocr_idx)
    full, _ = pasada_grande(path, pedir)

    # textos primero: así los eventos no cuentan los cambios de subtítulo
    hits, banda = None, None
    if not opts["sin_ocr"]:
        hits = ocr(full, fps, ocr_idx)
        banda = banda_subtitulos(hits) if hits else None
    eventos = eventos_en_planos(e, zonas, cuts, destellos, fps, (banda["y0"], banda["y1"]) if banda else None)
    ev_idx = eventos[:40]
    faltan = [i for i in ev_idx if i not in full]
    if faltan:
        full.update(pasada_grande(path, faltan)[0])

    planos, keys, labels = [], [], []
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < 2:
            continue
        mid = (a + b) // 2
        tr = tipo_transicion(frames, diff, a, fps) if a > 0 else "inicio"
        mv = movimiento(frames, a, b, fps)
        if mid in full:
            cv2.imwrite(str(d / "planos" / f"{k+1:03d}.jpg"), full[mid], [cv2.IMWRITE_JPEG_QUALITY, 85])
            keys.append(full[mid]); labels.append(f"#{k+1} {a/fps:.1f}s ({(b-a)/fps:.1f}) {mv['principal'][:12]}")
        planos.append({"n": k + 1, "inicio": r2(a / fps), "fin": r2(b / fps), "dura": r2((b - a) / fps),
                       "transicion_entrada": tr, "camara": mv, "eventos": sum(1 for x in eventos if a <= x < b),
                       "color": color_medio(frames[mid])})
    hoja(keys, labels, 6, d / "planos.jpg")
    hoja([full.get(i) for i in hook], [f"{i/fps:.1f}s" for i in hook], 10, d / "gancho.jpg", w=150)
    hoja([full.get(i) for i in ev_idx], [f"evento {i/fps:.1f}s" for i in ev_idx], 8, d / "eventos.jpg", w=170)
    for m, (c, ids) in enumerate(trans.items()):
        hoja([full.get(i) for i in ids], [f"{i/fps:.2f}s" for i in ids], 8, d / "transiciones" / f"{m+1:02d}.jpg", w=150)

    durs = [p["dura"] for p in planos] or [dur]
    cuts_t = [c / fps for c in cuts]
    # primer cambio visual: cuándo la imagen ya se alejó claramente del primer cuadro (transformación o corte)
    f0 = frames[0].astype(np.int16)
    primer_cambio = next((i / fps for i in range(1, min(n, int(fps * 6))) if np.abs(frames[i].astype(np.int16) - f0).mean() / 2.55 > 4.0), None)
    muestras = frames[:: max(1, int(fps))]
    datos = {"version": VERSION, "clave": clave, "archivo": path.name, "meta": meta,
             "ritmo": {"n_planos": len(planos), "plano_medio_s": r2(st.mean(durs)), "plano_mediana_s": r2(st.median(durs)),
                       "plano_min_s": r2(min(durs)), "plano_max_s": r2(max(durs)), "planos_largos_6s": sum(1 for x in durs if x > 6),
                       "cortes_por_min": r2(len(cuts) / max(1, dur) * 60, 1), "eventos_por_min": r2(len(eventos) / max(1, dur) * 60, 1),
                       "evento_cada_s": r2(dur / (len(cuts) + len(eventos) + 1)),
                       "primer_corte_s": r2(cuts_t[0]) if cuts_t else None, "primer_cambio_visual_s": r2(primer_cambio),
                       "destellos": len(destellos)},
             "planos": planos, "eventos_t": [r2(i / fps) for i in eventos], "cortes_t": [r2(t) for t in cuts_t],
             "transiciones": {}, "camara": {},
             "color": {"paleta": paleta(muestras), "acentos": acentos_vivos(frames[:: max(1, int(fps / 2))]), "grading": grading(muestras)},
             "layout": actividad(frames, d / "mapa_actividad.jpg")}
    for p in planos:
        datos["transiciones"][p["transicion_entrada"]] = datos["transiciones"].get(p["transicion_entrada"], 0) + 1
        datos["camara"][p["camara"]["principal"]] = datos["camara"].get(p["camara"]["principal"], 0) + 1
    datos["camara_viva_pct"] = round(100 * sum(1 for p in planos if p["camara"]["principal"] != "quieto") / max(1, len(planos)))

    if not opts["sin_ocr"]:
        if hits is None:
            datos["textos"] = {"error": "sin tesseract/pytesseract: no se leyeron textos"}
        else:
            datos["textos"] = {"lecturas": hits[:500], "subtitulos": banda}
            if banda:
                _, bandas = pasada_grande(path, [], (banda["y0"], banda["y1"]), banda_cada=max(1, int(round(fps / 15))))
                ab = analizar_banda(bandas, fps)
                if ab:
                    banda.update(ab)
                    sel = [k for k in sorted(bandas) if any(abs(k / fps - t) < 0.02 for t in ab["cambios_t"][:48])]
                    hoja([bandas[k] for k in sel], [f"{k/fps:.2f}s" for k in sel], 4, d / "subtitulos.jpg", w=360)
                tintas = [h["tinta"] for h in hits if abs(h["y_pct"] - banda["y_centro_pct"]) <= 8]
                banda["tinta_frecuente"] = max(set(tintas), key=tintas.count) if tintas else None
                banda["textos_fuera_de_subtitulo"] = sum(1 for h in hits if abs(h["y_pct"] - banda["y_centro_pct"]) > 9)

    if meta["tiene_audio"]:
        datos["audio"] = audio(path, cuts_t, dur, d)
        if datos["audio"] and not opts["sin_voz"]:
            datos["voz"] = transcribir(datos["audio"]["wav"])
    subs = (datos.get("textos") or {}).get("subtitulos") or {}
    if not (datos.get("voz") or {}).get("palabras_por_seg") and subs.get("karaoke_pct", 0) > 30:
        datos["voz_estimada"] = {"palabras_por_seg": subs.get("cambios_por_s"), "nota": "estimado: en karaoke cada cambio ≈ una palabra"}
    au = datos.get("audio") or {}
    linea_tiempo(dur, cuts_t, [i / fps for i in eventos], au.get("golpes", []), au.get("voz_cambios", []), subs.get("cambios_t", []), d / "linea_tiempo.png")
    datos["retencion"] = puntaje(datos)
    sb = storyboard_inverso(datos)
    (d / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1))
    (d / "storyboard.md").write_text(storyboard_md(sb))
    datos["segundos_analisis"] = round(time.time() - t0, 1)
    (d / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    return str(d), datos


def valores_retencion(dt):
    subs = ((dt.get("textos") or {}).get("subtitulos") or {})
    au = dt.get("audio") or {}
    return {"primer_cambio_visual_s": dt["ritmo"]["primer_cambio_visual_s"], "primer_corte_s": dt["ritmo"]["primer_corte_s"],
            "plano_mediana_s": dt["ritmo"]["plano_mediana_s"], "evento_cada_s": dt["ritmo"]["evento_cada_s"],
            "subtitulo_alto_px": subs.get("alto_px_1920"), "zona_ui_pct": dt["layout"]["zona_ui_pct"],
            "cortes_con_golpe_pct": au.get("cortes_con_golpe_pct"), "golpes_por_min": au.get("golpes_por_min")}


def puntaje(dt):
    v = valores_retencion(dt)
    return [{"regla": txt, "clave": k, "valor": v.get(k), "pasa": bool(fn(v.get(k)))} for k, txt, fn in RETENCION]


# ================================================================ gramática del estilo
def percentiles(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    return {f"p{p}": round(float(np.percentile(v, p)), 2) for p in (10, 25, 50, 75, 90)}


def gramatica(todos):
    """cómo se arma un video de este estilo: distribuciones y secuencias (la usa storyboard.py)"""
    planos = [p for d in todos for p in d["planos"]]
    tot = len(planos) or 1
    mix = lambda clave: {k: round(v / tot, 3) for k, v in sorted(
        {x: sum(1 for p in planos if clave(p) == x) for x in {clave(p) for p in planos}}.items(), key=lambda z: -z[1])}
    # secuencia de movimientos de cámara (qué viene después de qué)
    sig = {}
    for d in todos:
        movs = [p["camara"]["principal"] for p in d["planos"]]
        for a, b in zip(movs, movs[1:]):
            sig.setdefault(a, {}).setdefault(b, 0)
            sig[a][b] += 1
    sig = {a: {b: round(c / sum(v.values()), 3) for b, c in v.items()} for a, v in sig.items()}
    repite = [sum(1 for a, b in zip(m, m[1:]) if a == b) / max(1, len(m) - 1)
              for m in ([p["camara"]["principal"] for p in d["planos"]] for d in todos)]
    zooms = [abs((p["camara"].get("escala") or [1, 1])[1] - 1) * 100 for p in planos if p["camara"].get("escala")]
    paneos = [math.hypot((p["camara"].get("x_px") or [0, 0])[1], (p["camara"].get("y_px") or [0, 0])[1]) for p in planos]
    subs = [((d.get("textos") or {}).get("subtitulos") or {}) for d in todos]
    subs = [s for s in subs if s]
    aud = [d["audio"] for d in todos if d.get("audio")]
    tipos = {}
    for a in aud:
        for k, v in a["tipos_golpe"].items():
            tipos[k] = tipos.get(k, 0) + v
    ts = sum(tipos.values()) or 1
    voces = [d["voz"]["palabras_por_seg"] for d in todos if (d.get("voz") or {}).get("palabras_por_seg")] or \
            [d["voz_estimada"]["palabras_por_seg"] for d in todos if d.get("voz_estimada")]
    return {"version": VERSION, "referencias": len(todos), "planos_medidos": tot,
            "duracion_video_s": percentiles([d["meta"]["duracion"] for d in todos]),
            "duracion_plano_s": percentiles([p["dura"] for p in planos]),
            "transiciones": mix(lambda p: p["transicion_entrada"]),
            "camara": mix(lambda p: p["camara"]["principal"]),
            "camara_siguiente": sig, "camara_repite_seguida": media(repite, 3),
            "sacudida_pct": round(100 * sum(1 for p in planos if "sacudida" in p["camara"].get("tipo", "")) / tot, 1),
            "zoom_pct_por_plano": percentiles(zooms), "paneo_px_por_plano": percentiles(paneos),
            "easing": mix(lambda p: p["camara"].get("easing", "—")),
            "eventos_por_s": media([d["ritmo"]["eventos_por_min"] / 60 for d in todos], 3),
            "evento_cada_s": media([d["ritmo"]["evento_cada_s"] for d in todos]),
            "primer_cambio_visual_s": media([d["ritmo"]["primer_cambio_visual_s"] for d in todos]),
            "primer_corte_s": media([d["ritmo"]["primer_corte_s"] for d in todos]),
            "sfx_por_min": media([a["golpes_por_min"] for a in aud], 1), "sfx_tipos": {k: round(v / ts, 3) for k, v in tipos.items()},
            "cortes_con_golpe_pct": media([a["cortes_con_golpe_pct"] for a in aud], 1),
            "palabras_por_seg": media(voces), "subtitulo_cambios_por_s": media([s.get("cambios_por_s") for s in subs]),
            "mejoras": {"duracion_plano_s": [2.0, 4.5], "evento_cada_s_max": 2.0, "primer_cambio_visual_s_max": 0.8,
                        "primer_corte_s_max": 4.0, "cortes_con_golpe_pct_min": 80, "camara_repite_seguida_max": 0.25}}


# ================================================================ resumen, borrador e informe
def resumir(todos):
    tot = sum(d["ritmo"]["n_planos"] for d in todos) or 1
    trans, cam = {}, {}
    for d in todos:
        for k, v in d["transiciones"].items(): trans[k] = trans.get(k, 0) + v
        for k, v in d["camara"].items(): cam[k] = cam.get(k, 0) + v
    subs = [s for s in (((d.get("textos") or {}).get("subtitulos") or {}) for d in todos) if s]
    voces = [d["voz"] for d in todos if (d.get("voz") or {}).get("palabras_por_seg")]
    est = [d["voz_estimada"]["palabras_por_seg"] for d in todos if d.get("voz_estimada")]
    aud = [d["audio"] for d in todos if d.get("audio")]
    acentos = {}
    for d in todos:
        for a in d["color"]["acentos"]:
            acentos[a["hex"]] = acentos.get(a["hex"], 0) + a["pct_de_acentos"]
    reglas = []
    for k, txt, fn in RETENCION:
        vals = [valores_retencion(d).get(k) for d in todos]
        m = media(vals)
        reglas.append({"regla": txt, "clave": k, "valor": m, "pasa": bool(fn(m)), "pasan": f"{sum(1 for v in vals if fn(v))}/{len(vals)}"})
    tipos = {}
    for a in aud:
        for k, v in a["tipos_golpe"].items(): tipos[k] = tipos.get(k, 0) + v
    return {"version": VERSION, "referencias": len(todos), "duracion_media_s": media([d["meta"]["duracion"] for d in todos]),
            "fps": sorted({d["meta"]["fps"] for d in todos}), "tamano": sorted({f'{d["meta"]["ancho"]}x{d["meta"]["alto"]}' for d in todos}),
            "ritmo": {k: media([d["ritmo"][k] for d in todos]) for k in ("plano_medio_s", "plano_mediana_s", "cortes_por_min", "eventos_por_min",
                                                                         "evento_cada_s", "primer_corte_s", "primer_cambio_visual_s")},
            "transiciones_pct": {k: round(100 * v / tot, 1) for k, v in sorted(trans.items(), key=lambda z: -z[1])},
            "camara_pct": {k: round(100 * v / tot, 1) for k, v in sorted(cam.items(), key=lambda z: -z[1])},
            "camara_viva_pct": media([d["camara_viva_pct"] for d in todos], 0),
            "grading": {k: media([d["color"]["grading"][k] for d in todos], 1) for k in ("brillo_medio", "contraste", "saturacion_media", "temperatura", "negros_pct")},
            "fondos": {d["archivo"][:40]: [c["hex"] for c in d["color"]["paleta"] if c["rol"] == "fondo"][:3] for d in todos},
            "paletas": {d["archivo"][:40]: [c["hex"] for c in d["color"]["paleta"][:6]] for d in todos},
            "acentos": [h for h, _ in sorted(acentos.items(), key=lambda z: -z[1])[:6]],
            "layout": {k: media([d["layout"][k] for d in todos], 1) for k in ("arriba_pct", "centro_pct", "abajo_pct", "zona_ui_pct")},
            "subtitulos": {"y_centro_pct": media([s.get("y_centro_pct") for s in subs], 1), "alto_px_1920": media([s.get("alto_px_1920") for s in subs], 0),
                           "karaoke_pct": media([s.get("karaoke_pct") for s in subs], 0), "cambios_por_s": media([s.get("cambios_por_s") for s in subs]),
                           "resaltado_pct": media([s.get("resaltado_pct") for s in subs], 0),
                           "resaltado_hex": [s["resaltado_hex"] for s in subs if s.get("resaltado_hex")],
                           "tinta": [s["tinta_frecuente"] for s in subs if s.get("tinta_frecuente")],
                           "mayus_pct": media([s.get("mayus_pct") for s in subs], 0),
                           "texto_en_pantalla_pct": media([s.get("texto_en_pantalla_pct") for s in subs], 0)} if subs else None,
            "voz": {"palabras_por_seg": media([v["palabras_por_seg"] for v in voces]) or media(est),
                    "medida": "transcripción" if voces else ("estimada por subtítulos" if est else None),
                    "primera_palabra_s": media([v.get("primera_palabra_s") for v in voces]),
                    "ganchos": [v.get("gancho_3s") for v in voces], "cierres": [v.get("cierre") for v in voces]},
            "audio": {"lufs": media([a["lufs"] for a in aud], 1), "golpes_por_min": media([a["golpes_por_min"] for a in aud], 1),
                      "tipos_golpe": tipos, "cortes_con_golpe_pct": media([a["cortes_con_golpe_pct"] for a in aud], 1),
                      "voz_pct": media([a["voz_pct"] for a in aud], 1), "musica_fondo": [a["musica_fondo"] for a in aud]} if aud else None,
            "retencion": reglas}


def borrador_estilo(res, gram):
    s, a = res.get("subtitulos") or {}, res.get("audio") or {}
    return {"nombre": "COMPLETAR", "id": "COMPLETAR", "version": "0.1.0", "medido_con": f"extraer_estilo.py v{VERSION}",
            "formato": {"ancho": 1080, "alto": 1920, "fps": int(max(res["fps"])) if res["fps"] else 30,
                        "duracion_s": [round((res["duracion_media_s"] or 60) * 0.8), round((res["duracion_media_s"] or 60) * 1.15)]},
            "ritmo": {"medido": res["ritmo"], "objetivo_mejorado": gram["mejoras"]},
            "camara": {"medido": res["camara_pct"], "viva_pct": res["camara_viva_pct"], "zoom_pct_por_plano": gram["zoom_pct_por_plano"],
                       "paneo_px_por_plano": gram["paneo_px_por_plano"], "easing": gram["easing"]},
            "transiciones": {"medido_pct": res["transiciones_pct"]},
            "color": {"medido": res["grading"], "fondos": [h for v in res["fondos"].values() for h in v][:4], "acentos": res["acentos"],
                      "paletas_referencia": res["paletas"]},
            "subtitulos": {"medido": s, "fuente": "COMPLETAR (Fase B)",
                           "tamano_px": max(64, round((s.get("alto_px_1920") or 52) / 0.74)) if s else "COMPLETAR"},
            "sonido": {"medido": a, "reglas": {"cortes_con_golpe_pct_objetivo": 80}},
            "voz": res["voz"], "gramatica": gram, "retencion_original": res["retencion"],
            "recursos": "COMPLETAR (Fase B: catálogo de recursos)"}


def informe(res, gram, todos, carpetas, out, segundos):
    r, g = res["ritmo"], res["grading"]
    L = [f"# Informe de extracción (v{VERSION})", "",
         f"> Medidas automáticas en {segundos} s. La lectura visual (Fase B) y la prueba de clon (Fase D) las completa Claude.", "",
         f"**Referencias:** {res['referencias']} · **duración media:** {res['duracion_media_s']} s · **fps:** {res['fps']} · **tamaño:** {res['tamano']}", "",
         "## Tabla de retención (Fase E)", "", "| Regla | Valor medio | ¿El original cumple? | Referencias que pasan |", "|---|---|---|---|"]
    L += [f"| {x['regla']} | {x['valor']} | {'✅' if x['pasa'] else '❌ → [mejora]'} | {x['pasan']} |" for x in res["retencion"]]
    L += ["", "## Ritmo", "",
          f"- Plano medio **{r['plano_medio_s']} s** (mediana {r['plano_mediana_s']} s) · **{r['cortes_por_min']} cortes/min** · **{r['eventos_por_min']} eventos/min** dentro de los planos.",
          f"- Algo nuevo pasa cada **{r['evento_cada_s']} s** · primer cambio visual a los **{r['primer_cambio_visual_s']} s** · primer corte a los **{r['primer_corte_s']} s**.",
          f"- Duración de plano (p10 · p50 · p90): {gram['duracion_plano_s']['p10']} · {gram['duracion_plano_s']['p50']} · {gram['duracion_plano_s']['p90']} s.",
          "", "## Transiciones (% de planos)", ""] + [f"- {k}: {v}%" for k, v in res["transiciones_pct"].items()]
    L += ["", f"## Cámara (se mueve en el {res['camara_viva_pct']}% de los planos)", ""]
    L += [f"- {k}: {v}%" for k, v in res["camara_pct"].items()]
    zp, pp = gram["zoom_pct_por_plano"] or {}, gram["paneo_px_por_plano"] or {}
    L += [f"- Zoom por plano (p50 · p90): {zp.get('p50')} % · {zp.get('p90')} % · paneo por plano: {pp.get('p50')} px · {pp.get('p90')} px · sacudida en el {gram['sacudida_pct']}% de los planos.",
          f"- Mismo movimiento dos planos seguidos: {round((gram['camara_repite_seguida'] or 0)*100)}% · easing: " + ", ".join(f"{k} {round(v*100)}%" for k, v in gram["easing"].items())]
    L += ["", "## Color", "", f"- Brillo {g['brillo_medio']} · contraste {g['contraste']} · saturación {g['saturacion_media']} · temperatura {g['temperatura']} · negros {g['negros_pct']}%",
          "- Acentos vivos: " + " ".join(f"`{h}`" for h in res["acentos"])]
    L += [f"- {k}: " + " ".join(f"`{h}`" for h in v) + "  · fondos: " + " ".join(f"`{h}`" for h in res["fondos"].get(k, [])) for k, v in res["paletas"].items()]
    lay = res["layout"]
    L += ["", "## Composición", "", f"- Arriba {lay['arriba_pct']}% · centro {lay['centro_pct']}% · abajo {lay['abajo_pct']}% · zona de la interfaz (12 % de abajo) {lay['zona_ui_pct']}%"]
    s = res.get("subtitulos")
    if s:
        L += ["", "## Subtítulos", "",
              f"- Centro de la franja al **{s['y_centro_pct']}%** de la altura · alto de letra ≈ **{s['alto_px_1920']} px** a 1920 (≈ {round((s['alto_px_1920'] or 0)/0.74)} px de cuerpo).",
              f"- Karaoke (activa + dichas en otro tono) en el **{s['karaoke_pct']}%** del tiempo con texto · **{s['cambios_por_s']} cambios/s** · mayúsculas {s['mayus_pct']}% · hay texto el {s['texto_en_pantalla_pct']}% del video.",
              f"- Resaltado de color en el {s['resaltado_pct']}% del tiempo · " + " ".join(f"`{h}`" for h in s["resaltado_hex"]) + " · tinta " + " ".join(f"`{h}`" for h in s["tinta"])]
    v = res.get("voz") or {}
    if v.get("palabras_por_seg"):
        L += ["", "## Voz", "", f"- **{v['palabras_por_seg']} palabras por segundo** ({v['medida']})."]
        L += [f"- Gancho: “{x}”" for x in v["ganchos"] if x] + [f"- Cierre: “{x}”" for x in v["cierres"] if x]
    a = res.get("audio")
    if a:
        L += ["", "## Sonido", "", f"- {a['lufs']} LUFS · **{a['golpes_por_min']} golpes/min** · {a['cortes_con_golpe_pct']}% de cortes con golpe · voz {a['voz_pct']}% del tiempo · música de fondo: {a['musica_fondo']}",
              "- Tipos: " + ", ".join(f"{k} {n}" for k, n in sorted(a["tipos_golpe"].items(), key=lambda z: -z[1]))]
    L += ["", "## Qué copiar y qué mejorar", "", "**Copiar (identidad):** paleta y fondos, tipo de subtítulo, transiciones y movimientos más usados, mapa de sonido.", "", "**Mejorar ([mejora] en la guía):**"]
    L += [f"- {x['regla']} (el original da {x['valor']})." for x in res["retencion"] if not x["pasa"]] or ["- El original ya cumple todas las reglas medibles."]
    L += ["", "## Siguiente paso: afinar con storyboards", "",
          "```bash", "python3 storyboard.py esqueleto gramatica.json --duracion 75 --n 3   # 3 storyboards nuevos con la gramática",
          "python3 storyboard.py puntuar gramatica.json sb_*.json ref*/storyboard.json   # ranking y qué corregir", "```",
          "", "## Por referencia", ""]
    for d, c in zip(todos, carpetas):
        rr = d["ritmo"]
        L.append(f"- **{d['archivo'][:60]}** → `{Path(c).name}/` · {d['meta']['duracion']} s · {rr['n_planos']} planos · {rr['eventos_por_min']} eventos/min · {d['segundos_analisis']} s")
    out.write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Mide el estilo de uno o varios mp4.")
    ap.add_argument("fuente"); ap.add_argument("salida", nargs="?", default="estudio")
    ap.add_argument("--sin-ocr", action="store_true"); ap.add_argument("--sin-voz", action="store_true")
    ap.add_argument("--rapido", action="store_true"); ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--trabajos", type=int, default=0)
    a = ap.parse_args()
    src, out = Path(a.fuente).expanduser(), Path(a.salida).expanduser()
    if not which("ffmpeg") or not which("ffprobe"):
        sys.exit("Falta FFmpeg (instálalo y vuelve a correr).")
    vids = [src] if src.is_file() else sorted(p for p in src.iterdir() if p.suffix.lower() in VID_EXT)
    if not vids:
        sys.exit(f"No encontré videos en {src}")
    out.mkdir(parents=True, exist_ok=True)
    opts = {"sin_ocr": a.sin_ocr, "sin_voz": a.sin_voz, "rapido": a.rapido, "forzar": a.forzar}
    n = a.trabajos or max(1, min(len(vids), os.cpu_count() or 2))
    t0 = time.time()
    print(f"Analizando {len(vids)} video(s), {n} a la vez…")
    res_por = {}
    with ProcessPoolExecutor(max_workers=n) as ex:
        futs = {ex.submit(analizar, (str(v), str(out), i, opts)): i for i, v in enumerate(vids, 1)}
        for f in as_completed(futs):
            i = futs[f]
            try:
                c, d = f.result()
                res_por[i] = (c, d)
                print(f"  ✓ [{i}/{len(vids)}] {d['archivo'][:50]} · {d['segundos_analisis']} s" + (" (guardado)" if d["segundos_analisis"] == 0 else ""))
            except Exception as e:
                print(f"  ✗ [{i}/{len(vids)}] {vids[i-1].name[:50]}: {type(e).__name__}: {e}")
    if not res_por:
        sys.exit("No se pudo analizar ningún video.")
    orden = [res_por[k] for k in sorted(res_por)]
    carpetas, todos = [c for c, _ in orden], [d for _, d in orden]
    res, gram = resumir(todos), gramatica(todos)
    (out / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (out / "gramatica.json").write_text(json.dumps(gram, ensure_ascii=False, indent=1))
    (out / "estilo.borrador.json").write_text(json.dumps(borrador_estilo(res, gram), ensure_ascii=False, indent=1))
    seg = round(time.time() - t0)
    informe(res, gram, todos, carpetas, out / "Informe de extracción.md", seg)
    print(f"Listo en {seg} s → {out / 'Informe de extracción.md'}")


if __name__ == "__main__":
    main()
