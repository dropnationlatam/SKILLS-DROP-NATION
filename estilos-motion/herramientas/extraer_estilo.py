#!/usr/bin/env python3
"""
extraer_estilo.py  ·  Drop Nation · Skill Motion
Mide TODO lo medible de uno o varios mp4 de referencia para clonar su estilo.

Uso:
    python3 extraer_estilo.py <carpeta_o_mp4> [<salida>] [--sin-ocr] [--sin-voz]

Deja en <salida>/ (por defecto ./estudio):
    resumen.json                 números globales del estilo (todas las referencias)
    Informe de extracción.md     lo mismo en palabras, listo para escribir la guía
    <ref>/datos.json             todo lo medido de esa referencia
    <ref>/planos.jpg             hoja de contacto: un cuadro por plano, con tiempo
    <ref>/gancho.jpg             primeros 3 s a 10 cuadros por segundo
    <ref>/transiciones/NN.jpg    tira de cuadros alrededor de cada corte
    <ref>/mapa_actividad.jpg     dónde pasa el movimiento y el texto en pantalla
    <ref>/planos/NNN.jpg         cuadro del medio de cada plano (tamaño completo)

Requiere: ffmpeg/ffprobe, Python 3.10+, opencv-python, numpy, scikit-learn,
pillow, scenedetect. Opcional: pytesseract + tesseract (lee textos en pantalla),
faster-whisper (transcribe la voz y mide su ritmo).
"""
import json, math, os, re, subprocess, sys, shutil, statistics as st
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

AN_W = 180            # ancho de análisis (rápido)
VID_EXT = {".mp4", ".mov", ".m4v", ".webm"}


# ---------------------------------------------------------------- utilidades
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def hexc(rgb):
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, c))) for c in rgb)


def slug(name, i):
    s = re.sub(r"[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ ]+", "", Path(name).stem).strip()
    s = "_".join(s.split()[:5]) or "ref"
    return f"ref{i}_{s}"[:48]


def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,width,height,r_frame_rate:format=duration",
             "-of", "json", str(path)])
    j = json.loads(r.stdout or "{}")
    v = next((s for s in j.get("streams", []) if s["codec_type"] == "video"), {})
    a = any(s["codec_type"] == "audio" for s in j.get("streams", []))
    n, d = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    return {"ancho": v.get("width"), "alto": v.get("height"),
            "fps": round(float(n) / float(d or 1), 2),
            "duracion": round(float(j.get("format", {}).get("duration", 0)), 2),
            "tiene_audio": a}


# ---------------------------------------------------------------- lectura
def leer_cuadros(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    small, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h, w = f.shape[:2]
        small.append(cv2.resize(f, (AN_W, int(h * AN_W / w)), interpolation=cv2.INTER_AREA))
        i += 1
    cap.release()
    return np.array(small), fps


def cuadro_completo(path, t):
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    cap.release()
    return f if ok else None


# ---------------------------------------------------------------- cortes
def detectar_cortes(path, frames, fps):
    cuts = []
    try:
        from scenedetect import detect, ContentDetector, AdaptiveDetector
        a = detect(str(path), ContentDetector(threshold=24, min_scene_len=4))
        b = detect(str(path), AdaptiveDetector(adaptive_threshold=2.6, min_scene_len=4))
        for lst in (a, b):
            for s, _ in lst[1:]:
                cuts.append(getattr(s, 'frame_num', None) if hasattr(s, 'frame_num') else s.get_frames())
    except Exception:
        pass
    # respaldo propio: salto de histograma + diferencia de píxeles
    hsv = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
    hist = [cv2.normalize(cv2.calcHist([h], [0, 1], None, [24, 16], [0, 180, 0, 256]), None).flatten() for h in hsv]
    diff = np.zeros(len(frames))
    for i in range(1, len(frames)):
        hd = cv2.compareHist(hist[i - 1], hist[i], cv2.HISTCMP_BHATTACHARYYA)
        pd = np.mean(np.abs(frames[i].astype(int) - frames[i - 1].astype(int))) / 255
        diff[i] = 0.6 * hd + 0.4 * pd * 3
    thr = max(0.28, np.median(diff) + 6 * (np.median(np.abs(diff - np.median(diff))) + 1e-6))
    for i in range(1, len(diff) - 1):
        if diff[i] > thr and diff[i] >= diff[i - 1] and diff[i] >= diff[i + 1]:
            cuts.append(i)
    cuts = sorted(set(cuts))
    merged = []
    for c in cuts:
        if not merged or c - merged[-1] > max(3, int(fps * 0.15)):
            merged.append(c)
    return merged, diff


def tipo_transicion(frames, diff, c, fps):
    """corte seco / fundido / destello / barrido (whip) / zoom de transición"""
    w = int(fps * 0.25)
    seg = diff[max(1, c - w): min(len(diff), c + w + 1)]
    if len(seg) == 0:
        return "corte seco"
    peak = seg.max()
    spread = (seg > peak * 0.45).sum()
    lum = [frames[i].mean() for i in range(max(0, c - w), min(len(frames), c + w))]
    if lum and (max(lum) > 225 or max(lum) - np.median(lum) > 70):
        return "destello (flash a blanco)"
    if lum and min(lum) < 18:
        return "paso por negro"
    # desenfoque de movimiento alrededor del corte = barrido
    def sharp(i):
        g = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(g, cv2.CV_64F).var()
    try:
        s_cut = min(sharp(c - 1), sharp(c))
        s_ref = np.median([sharp(i) for i in range(max(0, c - w * 2), max(1, c - w))] or [s_cut])
        if s_ref > 0 and s_cut < s_ref * 0.35:
            return "barrido / desenfoque de movimiento"
    except Exception:
        pass
    if spread >= max(4, int(fps * 0.2)):
        return "fundido / transición suave"
    return "corte seco"


# ---------------------------------------------------------------- movimiento
def movimiento(frames, a, b, fps):
    """Ajusta una transformación (zoom, paneo, giro) cuadro a cuadro dentro del plano."""
    step = max(1, int(round(fps / 10)))
    zs, txs, tys, rots, mags = [], [], [], [], []
    prev = cv2.cvtColor(frames[a], cv2.COLOR_BGR2GRAY)
    for i in range(a + step, b, step):
        cur = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(prev, 200, 0.01, 5)
        if p0 is not None and len(p0) > 8:
            p1, stt, _ = cv2.calcOpticalFlowPyrLK(prev, cur, p0, None)
            g0, g1 = p0[stt == 1], p1[stt == 1]
            if len(g0) > 8:
                M, _ = cv2.estimateAffinePartial2D(g0, g1)
                if M is not None:
                    s = math.hypot(M[0, 0], M[1, 0])
                    zs.append(s); txs.append(M[0, 2]); tys.append(M[1, 2])
                    rots.append(math.degrees(math.atan2(M[1, 0], M[0, 0])))
                    mags.append(float(np.mean(np.linalg.norm(g1 - g0, axis=1))))
        prev = cur
    if not zs:
        return {"tipo": "sin datos"}
    dt = step / fps
    z_rate = (np.prod(zs) ** (1 / max(1e-6, len(zs) * dt)) - 1) * 100  # % por segundo
    scale_px = 1080 / AN_W
    pan_x = np.sum(txs) * scale_px / (len(txs) * dt)
    pan_y = np.sum(tys) * scale_px / (len(tys) * dt)
    rot = np.sum(rots) / (len(rots) * dt)
    agit = float(np.std(mags)) * scale_px
    tipo = []
    if z_rate > 1.5: tipo.append("acercamiento (push in)")
    if z_rate < -1.5: tipo.append("alejamiento (pull out)")
    if abs(pan_x) > 25: tipo.append("paneo " + ("izq→der" if pan_x < 0 else "der→izq"))
    if abs(pan_y) > 25: tipo.append("paneo vertical")
    if abs(rot) > 2: tipo.append("giro")
    if agit > 8: tipo.append("cámara nerviosa / sacudida")
    # curva de velocidad → easing
    prog = np.cumsum(np.abs(np.log(np.array(zs))) + np.hypot(txs, tys) / AN_W)
    easing = "—"
    if prog[-1] > 1e-3 and len(prog) >= 5:
        p = prog / prog[-1]
        x = np.linspace(0, 1, len(p))
        cands = {"lineal": x, "ease-out (frena al final)": 1 - (1 - x) ** 3,
                 "ease-in (acelera)": x ** 3,
                 "ease-in-out": np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)}
        easing = min(cands, key=lambda k: np.mean((cands[k] - p) ** 2))
    return {"tipo": ", ".join(tipo) or "quieto", "zoom_pct_por_s": round(float(z_rate), 2),
            "paneo_x_px_s": round(float(pan_x), 1), "paneo_y_px_s": round(float(pan_y), 1),
            "giro_grados_s": round(float(rot), 2), "sacudida": round(agit, 1), "easing": easing}


# ---------------------------------------------------------------- color
def paleta(imgs, k=8):
    from sklearn.cluster import KMeans
    px = np.concatenate([cv2.resize(i, (48, 85)).reshape(-1, 3) for i in imgs])
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(lab)
    out = []
    for ci in np.argsort(-np.bincount(km.labels_)):
        c = km.cluster_centers_[ci].astype(np.uint8).reshape(1, 1, 3)
        bgr = cv2.cvtColor(c, cv2.COLOR_LAB2BGR)[0, 0]
        hsv = cv2.cvtColor(bgr.reshape(1, 1, 3), cv2.COLOR_BGR2HSV)[0, 0]
        out.append({"hex": hexc(bgr[::-1]), "porcentaje": round(100 * np.mean(km.labels_ == ci), 1),
                    "saturacion": int(hsv[1]), "brillo": int(hsv[2])})
    return out


def grading(imgs):
    lab = [cv2.cvtColor(i, cv2.COLOR_BGR2LAB).astype(float) for i in imgs]
    hsv = [cv2.cvtColor(i, cv2.COLOR_BGR2HSV).astype(float) for i in imgs]
    return {"brillo_medio": round(np.mean([l[..., 0].mean() for l in lab]) / 2.55, 1),
            "contraste": round(np.mean([l[..., 0].std() for l in lab]) / 2.55, 1),
            "saturacion_media": round(np.mean([h[..., 1].mean() for h in hsv]) / 2.55, 1),
            "temperatura": round(np.mean([l[..., 2].mean() - 128 for l in lab]), 1),
            "nota_temperatura": "cálido" if np.mean([l[..., 2].mean() - 128 for l in lab]) > 4 else
                                ("frío" if np.mean([l[..., 2].mean() - 128 for l in lab]) < -4 else "neutro")}


# ---------------------------------------------------------------- texto
def ocr_textos(path, dur, cada=0.5):
    try:
        import pytesseract
    except Exception:
        return None
    langs = "spa+eng" if "spa" in (run(["tesseract", "--list-langs"]).stdout) else "eng"
    hits, t = [], 0.0
    while t < dur:
        f = cuadro_completo(path, t)
        t += cada
        if f is None:
            continue
        H, W = f.shape[:2]
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        for variante in (g, 255 - g):
            d = pytesseract.image_to_data(variante, lang=langs, config="--psm 11",
                                          output_type=pytesseract.Output.DICT)
            for i, txt in enumerate(d["text"]):
                txt = txt.strip()
                if len(txt) < 2 or float(d["conf"][i]) < 70 or not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9]", txt):
                    continue
                x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
                box = f[y:y + h, x:x + w].reshape(-1, 3)
                lum = box.mean(1)
                rell = box[lum >= np.percentile(lum, 80)].mean(0)[::-1] if len(box) else [0, 0, 0]
                borde = box[lum <= np.percentile(lum, 20)].mean(0)[::-1] if len(box) else [0, 0, 0]
                hits.append({"t": round(t - cada, 2), "texto": txt, "y_pct": round(100 * (y + h / 2) / H, 1),
                             "x_pct": round(100 * (x + w / 2) / W, 1),
                             "alto_px_1920": round(h * 1920 / H), "color_relleno": hexc(rell),
                             "color_borde": hexc(borde), "mayusculas": txt.isupper()})
    # agrupar en "subtítulos" (mismo texto seguido)
    caps = []
    for h in sorted(hits, key=lambda z: z["t"]):
        last = caps[-1] if caps else None
        if last and abs(h["t"] - last["fin"]) <= cada + 0.01 and abs(h["y_pct"] - last["y_pct"]) < 8:
            if h["texto"] not in last["palabras"]:
                last["palabras"].append(h["texto"])
            last["fin"] = h["t"]
        else:
            caps.append({"inicio": h["t"], "fin": h["t"], "y_pct": h["y_pct"], "palabras": [h["texto"]],
                         "alto_px_1920": h["alto_px_1920"], "relleno": h["color_relleno"],
                         "borde": h["color_borde"], "mayusculas": h["mayusculas"]})
    return {"lecturas": hits, "bloques": caps}


# ---------------------------------------------------------------- audio
def audio(path, cuts_t, tmp):
    wav = tmp / "a.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", str(wav)])
    if not wav.exists():
        return None
    import wave
    with wave.open(str(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    sr, hop = 16000, 320  # 20 ms
    n = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    # flujo espectral para golpes / efectos
    win = 1024
    spec, prev = [], None
    for i in range(0, len(x) - win, hop):
        m = np.abs(np.fft.rfft(x[i:i + win] * np.hanning(win)))
        if prev is not None:
            spec.append(np.sum(np.maximum(0, m - prev)))
        prev = m
    flux = np.array(spec)
    on = []
    if len(flux):
        thr = np.median(flux) + 3 * np.std(flux)
        for i in range(1, len(flux) - 1):
            if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]:
                t = i * hop / sr
                if not on or t - on[-1] > 0.12:
                    on.append(round(t, 2))
    dur = len(x) / sr
    en_corte = sum(1 for c in cuts_t if any(abs(c - o) < 0.09 for o in on))
    lufs = None
    r = run(["ffmpeg", "-v", "info", "-i", str(path), "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?\d+\.\d) LUFS", r.stderr)
    if m:
        lufs = float(m[-1])
    piso = float(np.percentile(db, 10))
    silencio = float(np.mean(db < -45) * 100)
    return {"lufs": lufs, "golpes_por_min": round(len(on) / dur * 60, 1), "golpes_t": on,
            "cortes_con_golpe_pct": round(100 * en_corte / max(1, len(cuts_t)), 1),
            "piso_db": round(piso, 1), "silencio_pct": round(silencio, 1),
            "hay_fondo_continuo": piso > -42,
            "nota_fondo": "hay música/ambiente de fondo constante" if piso > -42 else "voz sola o con huecos (sin cama musical fuerte)",
            "wav": str(wav)}


def transcribir(wav):
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
        segs, _ = m.transcribe(wav, language="es", word_timestamps=True, vad_filter=True)
        words, texto = [], []
        for s in segs:
            texto.append(s.text.strip())
            for w in (s.words or []):
                words.append({"p": w.word.strip(), "i": round(w.start, 2), "f": round(w.end, 2)})
        if not words:
            return None
        habl = sum(w["f"] - w["i"] for w in words)
        pausas = [words[i + 1]["i"] - words[i]["f"] for i in range(len(words) - 1)]
        return {"texto": " ".join(texto), "palabras": words,
                "palabras_por_seg": round(len(words) / max(0.1, words[-1]["f"] - words[0]["i"]), 2),
                "primera_palabra_s": words[0]["i"], "pausa_media_s": round(st.mean(pausas), 2) if pausas else 0,
                "gancho_3s": " ".join(w["p"] for w in words if w["i"] < 3.0)}
    except Exception as e:
        return {"error": f"no se pudo transcribir ({type(e).__name__}): instala faster-whisper o revisa la red"}


# ---------------------------------------------------------------- imágenes
def hoja(imgs, labels, cols, out, w=240):
    if not imgs:
        return
    h = int(imgs[0].shape[0] * w / imgs[0].shape[1])
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + 26)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    f = font(16)
    for i, (im, lb) in enumerate(zip(imgs, labels)):
        r, c = divmod(i, cols)
        sheet.paste(Image.fromarray(cv2.cvtColor(cv2.resize(im, (w, h)), cv2.COLOR_BGR2RGB)), (c * w, r * (h + 26) + 26))
        d.text((c * w + 6, r * (h + 26) + 4), lb, fill=(255, 220, 0), font=f)
    sheet.save(out, quality=88)


def mapa_actividad(frames, out):
    acc = np.zeros(frames[0].shape[:2], float)
    for i in range(1, len(frames), 2):
        acc += np.abs(frames[i].astype(float) - frames[i - 1].astype(float)).mean(2)
    acc = (255 * acc / (acc.max() + 1e-6)).astype(np.uint8)
    heat = cv2.applyColorMap(cv2.resize(acc, (360, int(360 * acc.shape[0] / acc.shape[1]))), cv2.COLORMAP_INFERNO)
    H = heat.shape[0]
    for p in (10, 20, 80, 90):  # zonas seguras de reels (arriba/abajo)
        cv2.line(heat, (0, int(H * p / 100)), (360, int(H * p / 100)), (255, 255, 255), 1)
    cv2.imwrite(str(out), heat)
    filas = acc.mean(1)
    tercios = [float(filas[:len(filas)//3].mean()), float(filas[len(filas)//3:2*len(filas)//3].mean()), float(filas[2*len(filas)//3:].mean())]
    s = sum(tercios) + 1e-6
    return {"arriba_pct": round(100 * tercios[0] / s), "centro_pct": round(100 * tercios[1] / s), "abajo_pct": round(100 * tercios[2] / s)}


# ---------------------------------------------------------------- por referencia
def analizar(path, outdir, idx, con_ocr, con_voz):
    meta = probe(path)
    d = outdir / slug(path.name, idx)
    (d / "planos").mkdir(parents=True, exist_ok=True)
    (d / "transiciones").mkdir(exist_ok=True)
    print(f"  · leyendo cuadros de {path.name}")
    frames, fps = leer_cuadros(path)
    cuts, diff = detectar_cortes(path, frames, fps)
    bounds = [0] + cuts + [len(frames)]
    planos, keys, labels = [], [], []
    print(f"  · {len(bounds)-1} planos: midiendo movimiento y color")
    for n in range(len(bounds) - 1):
        a, b = bounds[n], bounds[n + 1]
        if b - a < 2:
            continue
        mid = (a + b) // 2
        t0, t1 = a / fps, b / fps
        full = cuadro_completo(path, mid / fps)
        if full is not None:
            cv2.imwrite(str(d / "planos" / f"{n+1:03d}.jpg"), full, [cv2.IMWRITE_JPEG_QUALITY, 85])
            keys.append(full); labels.append(f"#{n+1} {t0:.1f}s ({t1-t0:.1f})")
        planos.append({"n": n + 1, "inicio": round(t0, 2), "fin": round(t1, 2), "dura": round(t1 - t0, 2),
                       "transicion_entrada": tipo_transicion(frames, diff, a, fps) if a > 0 else "inicio",
                       "movimiento": movimiento(frames, a, b, fps),
                       "colores": [c["hex"] for c in paleta([frames[mid]], k=3)],
                       "brillo": round(float(cv2.cvtColor(frames[mid], cv2.COLOR_BGR2LAB)[..., 0].mean() / 2.55), 1)})
    hoja(keys, labels, 6, d / "planos.jpg")
    # gancho: primeros 3 s a 10 cps
    g = [cuadro_completo(path, t / 10) for t in range(30)]
    hoja([x for x in g if x is not None], [f"{t/10:.1f}s" for t in range(30)], 10, d / "gancho.jpg", w=160)
    # transiciones: ±0,3 s alrededor de cada corte
    for n, c in enumerate(cuts[:60]):
        ts = [c / fps + dt for dt in (-0.3, -0.2, -0.1, -0.033, 0, 0.1, 0.2, 0.3)]
        ims = [cuadro_completo(path, max(0, t)) for t in ts]
        hoja([x for x in ims if x is not None], [f"{t:.2f}s" for t in ts], 8, d / "transiciones" / f"{n+1:02d}.jpg", w=150)
    muestras = frames[:: max(1, int(fps))]
    datos = {"archivo": path.name, "meta": meta, "planos": planos,
             "ritmo": {"n_planos": len(planos),
                       "plano_medio_s": round(st.mean([p["dura"] for p in planos]), 2) if planos else 0,
                       "plano_mediana_s": round(st.median([p["dura"] for p in planos]), 2) if planos else 0,
                       "plano_min_s": min((p["dura"] for p in planos), default=0),
                       "plano_max_s": max((p["dura"] for p in planos), default=0),
                       "cortes_por_min": round(len(cuts) / max(1, meta["duracion"]) * 60, 1),
                       "cortes_primeros_3s": sum(1 for c in cuts if c / fps < 3),
                       "primer_corte_s": round(cuts[0] / fps, 2) if cuts else None},
             "transiciones": {}, "paleta": paleta(muestras), "grading": grading(muestras),
             "layout": mapa_actividad(frames, d / "mapa_actividad.jpg")}
    for p in planos:
        datos["transiciones"][p["transicion_entrada"]] = datos["transiciones"].get(p["transicion_entrada"], 0) + 1
    mov = {}
    for p in planos:
        for t in p["movimiento"].get("tipo", "").split(", "):
            mov[t] = mov.get(t, 0) + 1
    datos["movimiento_resumen"] = mov
    if con_ocr:
        print("  · leyendo textos en pantalla (OCR)")
        datos["textos"] = ocr_textos(path, meta["duracion"])
    if meta["tiene_audio"]:
        print("  · analizando audio")
        datos["audio"] = audio(path, [c / fps for c in cuts], d)
        if con_voz and datos["audio"]:
            print("  · transcribiendo voz")
            datos["voz"] = transcribir(datos["audio"]["wav"])
    (d / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    return d, datos


# ---------------------------------------------------------------- resumen global
def resumir(todos):
    def m(vals):
        vals = [v for v in vals if v is not None]
        return round(st.mean(vals), 2) if vals else None
    trans, movs = {}, {}
    for d in todos:
        for k, v in d["transiciones"].items(): trans[k] = trans.get(k, 0) + v
        for k, v in d["movimiento_resumen"].items(): movs[k] = movs.get(k, 0) + v
    tot_p = sum(d["ritmo"]["n_planos"] for d in todos) or 1
    caps = [b for d in todos if d.get("textos") for b in d["textos"]["bloques"]]
    sub = None
    if caps:
        dur_c = [b["fin"] - b["inicio"] + 0.5 for b in caps]
        sub = {"bloques_leidos": len(caps),
               "y_pct_mediana": round(st.median(b["y_pct"] for b in caps), 1),
               "alto_px_mediana": round(st.median(b["alto_px_1920"] for b in caps)),
               "palabras_por_bloque": round(st.mean(len(b["palabras"]) for b in caps), 1),
               "segundos_en_pantalla": round(st.mean(dur_c), 2),
               "mayusculas_pct": round(100 * st.mean(1 if b["mayusculas"] else 0 for b in caps)),
               "relleno_frecuente": max(set(b["relleno"] for b in caps), key=[b["relleno"] for b in caps].count),
               "borde_frecuente": max(set(b["borde"] for b in caps), key=[b["borde"] for b in caps].count)}
    voz = [d["voz"] for d in todos if d.get("voz") and "palabras_por_seg" in d["voz"]]
    aud = [d["audio"] for d in todos if d.get("audio")]
    return {"referencias": len(todos),
            "duracion_media_s": m([d["meta"]["duracion"] for d in todos]),
            "fps": sorted({d["meta"]["fps"] for d in todos}),
            "ritmo": {"plano_medio_s": m([d["ritmo"]["plano_medio_s"] for d in todos]),
                      "plano_mediana_s": m([d["ritmo"]["plano_mediana_s"] for d in todos]),
                      "cortes_por_min": m([d["ritmo"]["cortes_por_min"] for d in todos]),
                      "cortes_primeros_3s": m([d["ritmo"]["cortes_primeros_3s"] for d in todos]),
                      "primer_corte_s": m([d["ritmo"]["primer_corte_s"] for d in todos])},
            "transiciones_pct": {k: round(100 * v / tot_p, 1) for k, v in sorted(trans.items(), key=lambda z: -z[1])},
            "movimiento_pct": {k: round(100 * v / tot_p, 1) for k, v in sorted(movs.items(), key=lambda z: -z[1])},
            "grading": {k: m([d["grading"][k] for d in todos]) for k in ("brillo_medio", "contraste", "saturacion_media", "temperatura")},
            "layout": {k: m([d["layout"][k] for d in todos]) for k in ("arriba_pct", "centro_pct", "abajo_pct")},
            "paletas": {d["archivo"][:40]: [c["hex"] for c in d["paleta"][:6]] for d in todos},
            "subtitulos": sub,
            "voz": {"palabras_por_seg": m([v["palabras_por_seg"] for v in voz]),
                    "primera_palabra_s": m([v["primera_palabra_s"] for v in voz]),
                    "ganchos": [v["gancho_3s"] for v in voz]} if voz else None,
            "audio": {"lufs": m([a["lufs"] for a in aud]), "golpes_por_min": m([a["golpes_por_min"] for a in aud]),
                      "cortes_con_golpe_pct": m([a["cortes_con_golpe_pct"] for a in aud]),
                      "fondo_continuo": [a["hay_fondo_continuo"] for a in aud]} if aud else None}


def informe(res, todos, carpetas, out):
    L = ["# Informe de extracción", "",
         "> Generado por `extraer_estilo.py`. Son **medidas**; la lectura visual (Fase B) y la prueba de clon (Fase C) las completa Claude.", "",
         f"**Referencias:** {res['referencias']} · **duración media:** {res['duracion_media_s']} s · **fps:** {res['fps']}", "",
         "## Ritmo", ""]
    r = res["ritmo"]
    L += [f"- Plano medio **{r['plano_medio_s']} s** (mediana {r['plano_mediana_s']} s) → **{r['cortes_por_min']} cortes por minuto**.",
          f"- Cortes en los primeros 3 s: **{r['cortes_primeros_3s']}** · primer corte a los **{r['primer_corte_s']} s**.", "",
          "## Transiciones (% de planos)", ""]
    L += [f"- {k}: {v}%" for k, v in res["transiciones_pct"].items()]
    L += ["", "## Cámara / movimiento (% de planos)", ""] + [f"- {k}: {v}%" for k, v in res["movimiento_pct"].items()]
    g = res["grading"]
    L += ["", "## Color", "", f"- Brillo {g['brillo_medio']} · contraste {g['contraste']} · saturación {g['saturacion_media']} · temperatura {g['temperatura']} (− frío / + cálido)"]
    for k, v in res["paletas"].items():
        L.append(f"- {k}: " + " ".join(f"`{h}`" for h in v))
    lay = res["layout"]
    L += ["", "## Dónde pasa la acción (vertical)", "", f"- Arriba {lay['arriba_pct']}% · centro {lay['centro_pct']}% · abajo {lay['abajo_pct']}% (ver `mapa_actividad.jpg`)"]
    if res["subtitulos"]:
        s = res["subtitulos"]
        L += ["", "## Textos / subtítulos (OCR)", "",
              f"- Altura en pantalla (centro): **{s['y_pct_mediana']}%** desde arriba · alto de letra ≈ **{s['alto_px_mediana']} px** en 1920.",
              f"- **{s['palabras_por_bloque']} palabras por bloque**, **{s['segundos_en_pantalla']} s** en pantalla · mayúsculas {s['mayusculas_pct']}%.",
              f"- Relleno frecuente `{s['relleno_frecuente']}` · borde/sombra `{s['borde_frecuente']}`."]
    if res["voz"]:
        v = res["voz"]
        L += ["", "## Voz", "", f"- **{v['palabras_por_seg']} palabras por segundo** · primera palabra a los {v['primera_palabra_s']} s."]
        L += [f"- Gancho: “{x}”" for x in v["ganchos"]]
    if res["audio"]:
        a = res["audio"]
        L += ["", "## Sonido", "", f"- Volumen {a['lufs']} LUFS · **{a['golpes_por_min']} golpes/efectos por minuto** · {a['cortes_con_golpe_pct']}% de los cortes llevan golpe.",
              f"- Fondo continuo (música/ambiente): {a['fondo_continuo']}"]
    L += ["", "## Por referencia", ""]
    for d, c in zip(todos, carpetas):
        rr = d["ritmo"]
        L.append(f"- **{d['archivo'][:60]}** → `{c.name}/` · {d['meta']['duracion']} s · {rr['n_planos']} planos · {rr['cortes_por_min']} cortes/min")
    out.write_text("\n".join(L) + "\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    src = Path(args[0]).expanduser()
    out = Path(args[1] if len(args) > 1 else "estudio").expanduser()
    out.mkdir(parents=True, exist_ok=True)
    vids = [src] if src.is_file() else sorted(p for p in src.iterdir() if p.suffix.lower() in VID_EXT)
    if not vids:
        print("No encontré mp4 en", src); sys.exit(1)
    todos, carpetas = [], []
    for i, v in enumerate(vids, 1):
        print(f"[{i}/{len(vids)}] {v.name}")
        c, d = analizar(v, out, i, "--sin-ocr" not in sys.argv, "--sin-voz" not in sys.argv)
        todos.append(d); carpetas.append(c)
    res = resumir(todos)
    (out / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    informe(res, todos, carpetas, out / "Informe de extracción.md")
    print("Listo →", out / "Informe de extracción.md")


if __name__ == "__main__":
    main()
